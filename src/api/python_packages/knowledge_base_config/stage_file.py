import fcntl
import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from typing import Iterator

logger = logging.getLogger(__name__)

FILE_STAGE_RETRIES = max(
    1,
    int(os.getenv("KNOWLEDGE_BASE_FILE_READ_RETRIES", "5")),
)
FILE_STAGE_RETRY_DELAY_SECONDS = float(
    os.getenv("KNOWLEDGE_BASE_FILE_READ_RETRY_DELAY_SECONDS", "5")
)
FILE_STAGE_MIN_SIZE_BYTES = max(
    1,
    int(os.getenv("KNOWLEDGE_BASE_FILE_MIN_SIZE_BYTES", "1")),
)
FILE_STAGE_COPY_TIMEOUT_SECONDS = max(
    30,
    int(os.getenv("KNOWLEDGE_BASE_FILE_COPY_TIMEOUT_SECONDS", "300")),
)

PRIMARY_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../../..",
    "knowledge_base",
    "files",
    ".staged",
)
FALLBACK_CACHE_DIR = "/tmp/knowledge_base_staged"


def _get_cache_dir() -> str:
    """Return a usable directory for persistent staged files."""
    for path in (PRIMARY_CACHE_DIR, FALLBACK_CACHE_DIR):
        try:
            os.makedirs(path, exist_ok=True)
            test_file = os.path.join(path, ".write_test")
            with open(test_file, "w") as f:
                f.write("ok")
            os.unlink(test_file)
            return path
        except OSError:
            continue
    return FALLBACK_CACHE_DIR


def is_mounted_or_symlink(filepath: str | None) -> bool:
    """Check if the given file path is a symlink or located in a mount directory."""
    if not filepath:
        return False
    if os.path.islink(filepath):
        return True
    abs_path = os.path.abspath(filepath)
    return f"{os.sep}.mnt{os.sep}" in abs_path or f"{os.sep}mnt{os.sep}" in abs_path


def _get_cache_path(source_path: str, cache_dir: str) -> str:
    """Generate a stable, unique cache file path based on source path."""
    source_hash = hashlib.sha256(source_path.encode("utf-8")).hexdigest()[:12]
    base_name = os.path.basename(source_path)
    clean_name = "".join(c for c in base_name if c.isalnum() or c in "._- ") or "file"
    return os.path.join(cache_dir, f"{source_hash}_{clean_name}")


def _safe_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return -1


def _infer_rclone_source(source_path: str) -> str | None:
    """Map ``.../.mnt/<remote>/<relpath>`` to ``remote:relpath`` when rclone knows that remote."""
    rclone_bin = shutil.which("rclone")
    if not rclone_bin:
        return None

    abs_path = os.path.abspath(source_path)
    marker = f"{os.sep}.mnt{os.sep}"
    if marker not in abs_path:
        return None

    rest = abs_path.split(marker, 1)[1]
    remote, sep, relpath = rest.partition(os.sep)
    if not remote or not sep:
        return None

    try:
        listed = subprocess.run(
            [rclone_bin, "listremotes"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    remotes = [
        line.strip().rstrip(":")
        for line in listed.stdout.splitlines()
        if line.strip()
    ]
    if remote not in remotes:
        logger.debug(
            "rclone remote '%s' is not in listremotes; skip Drive API export",
            remote,
        )
        return None
    return f"{remote}:{relpath}"


def _copy_with_rclone(rclone_source: str, tmp_path: str) -> bool:
    """Export a Google native document through rclone Drive API (not FUSE)."""
    rclone_bin = shutil.which("rclone")
    if not rclone_bin:
        return False

    if os.path.exists(tmp_path):
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    logger.info(
        "Exporting '%s' with rclone copyto (timeout %ss)",
        rclone_source,
        FILE_STAGE_COPY_TIMEOUT_SECONDS,
    )
    result = subprocess.run(
        [
            rclone_bin,
            "copyto",
            "--ignore-size",
            "--drive-export-formats",
            "docx,xlsx,pdf",
            rclone_source,
            tmp_path,
        ],
        capture_output=True,
        text=True,
        timeout=FILE_STAGE_COPY_TIMEOUT_SECONDS,
    )
    size = _safe_size(tmp_path)
    if result.returncode == 0 and size >= FILE_STAGE_MIN_SIZE_BYTES:
        logger.info("rclone copyto wrote %d bytes from '%s'", size, rclone_source)
        return True

    stderr = (result.stderr or "").strip()
    logger.warning(
        "rclone copyto failed for '%s': code=%s size=%s stderr=%s",
        rclone_source,
        result.returncode,
        size,
        stderr[:500],
    )
    return False


def _copy_with_cat(source_path: str, tmp_path: str) -> bool:
    """
    Capture a single sequential read from FUSE into a local file.

    Native Google Docs/Sheets appear as 0-byte files on rclone mount. Python
    ``open()`` can abort the export stream; ``cat`` stdout must be saved on
    the first read — do not discard it and retry.
    """
    if os.path.exists(tmp_path):
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    logger.info(
        "Copying mounted file '%s' with sequential cat (timeout %ss)",
        source_path,
        FILE_STAGE_COPY_TIMEOUT_SECONDS,
    )
    with open(tmp_path, "wb") as destination:
        result = subprocess.run(
            ["cat", "--", source_path],
            stdout=destination,
            stderr=subprocess.PIPE,
            timeout=FILE_STAGE_COPY_TIMEOUT_SECONDS,
        )
        destination.flush()
        os.fsync(destination.fileno())

    size = _safe_size(tmp_path)
    if result.returncode == 0 and size >= FILE_STAGE_MIN_SIZE_BYTES:
        logger.info("cat wrote %d bytes from '%s'", size, source_path)
        return True

    stderr = (result.stderr or b"").decode("utf-8", errors="replace").strip()
    logger.warning(
        "cat copy failed for '%s': code=%s size=%s stderr=%s",
        source_path,
        result.returncode,
        size,
        stderr[:500],
    )
    return False


def _copy_mounted_file(
    source_path: str,
    tmp_path: str,
    rclone_source: str | None,
) -> bool:
    """Try rclone Drive API export first, then a single sequential cat of the mount."""
    sources_to_try: list[str] = []
    if rclone_source:
        sources_to_try.append(rclone_source)
    inferred = _infer_rclone_source(source_path)
    if inferred and inferred not in sources_to_try:
        sources_to_try.append(inferred)

    for source in sources_to_try:
        try:
            if _copy_with_rclone(source, tmp_path):
                return True
        except (OSError, subprocess.SubprocessError) as error:
            logger.warning("rclone export error for '%s': %s", source, error)

    try:
        return _copy_with_cat(source_path, tmp_path)
    except (OSError, subprocess.SubprocessError) as error:
        logger.warning("cat copy error for '%s': %s", source_path, error)
        return False


def stage_file(
    filepath: str,
    force_update: bool = False,
    rclone_source: str | None = None,
) -> str:
    """
    Ensure a mounted or symlinked file is copied to a persistent local cache.
    Uses file locking to prevent concurrent read/write races on the same file.
    """
    if not filepath:
        raise FileNotFoundError("No file path was configured")

    source_path = os.path.realpath(filepath) if os.path.islink(filepath) else filepath
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"File not found: {filepath}")
    if os.path.isdir(source_path):
        raise IsADirectoryError(f"Expected a file, got directory: {filepath}")

    if not is_mounted_or_symlink(filepath):
        return source_path

    cache_dir = _get_cache_dir()
    cached_path = _get_cache_path(source_path, cache_dir)
    lock_path = f"{cached_path}.lock"

    with open(lock_path, "w") as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX)

            source_size = _safe_size(source_path)
            cache_ok = (
                os.path.exists(cached_path)
                and _safe_size(cached_path) >= FILE_STAGE_MIN_SIZE_BYTES
            )

            # Google native docs report size 0 on the mount. Re-reading them
            # through FUSE is unreliable; keep a good cache unless forced.
            if cache_ok and not force_update:
                if source_size == 0:
                    logger.info(
                        "Using staged cache '%s' for 0-byte mounted file '%s'",
                        cached_path,
                        filepath,
                    )
                    return cached_path
                try:
                    if os.path.getmtime(cached_path) >= os.path.getmtime(source_path):
                        logger.debug("Staged file cache is up-to-date: '%s'", cached_path)
                        return cached_path
                except OSError:
                    logger.debug(
                        "Using existing cache for '%s' without mtime check", filepath
                    )
                    return cached_path

            last_error = None
            for attempt in range(1, FILE_STAGE_RETRIES + 1):
                tmp_fd, tmp_path = tempfile.mkstemp(
                    prefix="stage_",
                    suffix=".tmp",
                    dir=cache_dir,
                )
                os.close(tmp_fd)

                try:
                    success = _copy_mounted_file(
                        source_path, tmp_path, rclone_source
                    )
                    if success:
                        try:
                            source_mtime = os.path.getmtime(source_path)
                            os.utime(tmp_path, (source_mtime, source_mtime))
                        except OSError:
                            pass

                        os.replace(tmp_path, cached_path)
                        logger.info(
                            "Staged file '%s' for reading at '%s' on attempt %d (%d bytes)",
                            filepath,
                            cached_path,
                            attempt,
                            os.path.getsize(cached_path),
                        )
                        return cached_path

                    staged_size = _safe_size(tmp_path)
                    raise OSError(f"The staged file is too small ({max(staged_size, 0)} bytes)")
                except (OSError, shutil.Error, subprocess.SubprocessError) as error:
                    last_error = error
                    if os.path.exists(tmp_path):
                        try:
                            os.unlink(tmp_path)
                        except OSError:
                            pass

                    if cache_ok:
                        logger.warning(
                            "Unable to refresh staged file '%s' (%s); falling back to existing cache '%s'",
                            filepath,
                            error,
                            cached_path,
                        )
                        return cached_path

                    logger.warning(
                        "Unable to stage file '%s' on attempt %d/%d: %s",
                        filepath,
                        attempt,
                        FILE_STAGE_RETRIES,
                        error,
                    )
                    if attempt < FILE_STAGE_RETRIES:
                        time.sleep(FILE_STAGE_RETRY_DELAY_SECONDS * attempt)

            raise OSError(
                f"Unable to read '{filepath}' after {FILE_STAGE_RETRIES} attempts"
            ) from last_error

        finally:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
            except OSError:
                pass


@contextmanager
def stage_file_for_read(
    filepath: str,
    force_update: bool = False,
    rclone_source: str | None = None,
) -> Iterator[str]:
    """
    Context manager for reading staged files.
    Preserves the cached file on disk across calls.
    """
    staged_path = stage_file(
        filepath, force_update=force_update, rclone_source=rclone_source
    )
    yield staged_path
