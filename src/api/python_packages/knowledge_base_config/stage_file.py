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
    int(os.getenv("KNOWLEDGE_BASE_FILE_READ_RETRIES", "3")),
)
FILE_STAGE_RETRY_DELAY_SECONDS = float(
    os.getenv("KNOWLEDGE_BASE_FILE_READ_RETRY_DELAY_SECONDS", "2")
)
FILE_STAGE_MIN_SIZE_BYTES = max(
    1,
    int(os.getenv("KNOWLEDGE_BASE_FILE_MIN_SIZE_BYTES", "1")),
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


def _copy_mounted_file(source_path: str, tmp_path: str) -> bool:
    """
    Attempt to copy a file from a mounted remote path to a local temporary path.
    Tries Python streaming first, falling back to shell `cat` redirection which
    is particularly effective at pulling streams from FUSE mounts without seeking.
    """
    # Method 1: Python streaming read
    try:
        with open(source_path, "rb") as source, open(tmp_path, "wb") as destination:
            shutil.copyfileobj(source, destination, length=1024 * 1024)
            destination.flush()
            os.fsync(destination.fileno())

        if os.path.getsize(tmp_path) >= FILE_STAGE_MIN_SIZE_BYTES:
            return True
    except (OSError, shutil.Error) as err:
        logger.debug("Python copy failed for '%s': %s; trying shell cat", source_path, err)

    # Method 2: Shell `cat` streaming directly to target file
    # This avoids seek/partial read issues common in FUSE Google Drive mounts
    try:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        cmd = f"cat '{source_path}' > '{tmp_path}'"
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=120,
        )
        if (
            result.returncode == 0
            and os.path.exists(tmp_path)
            and os.path.getsize(tmp_path) >= FILE_STAGE_MIN_SIZE_BYTES
        ):
            return True
        else:
            stderr_msg = result.stderr.decode("utf-8", errors="replace").strip()
            logger.debug(
                "Shell cat copy failed for '%s': code=%d, stderr=%s",
                source_path,
                result.returncode,
                stderr_msg,
            )
    except Exception as err:
        logger.debug("Shell cat execution error for '%s': %s", source_path, err)

    return False


def stage_file(filepath: str, force_update: bool = False) -> str:
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

    # Acquire an exclusive lock during staging to prevent concurrent threads/workers from colliding
    with open(lock_path, "w") as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX)

            # Check if cache already exists and is fresh
            if (
                os.path.exists(cached_path)
                and os.path.getsize(cached_path) >= FILE_STAGE_MIN_SIZE_BYTES
            ):
                if not force_update:
                    try:
                        source_mtime = os.path.getmtime(source_path)
                        cached_mtime = os.path.getmtime(cached_path)
                        if cached_mtime >= source_mtime:
                            logger.debug("Staged file cache is up-to-date: '%s'", cached_path)
                            return cached_path
                    except OSError:
                        logger.debug(
                            "Using existing cache for '%s' without mtime check", filepath
                        )
                        return cached_path

            # Attempt to copy with retries
            last_error = None
            for attempt in range(1, FILE_STAGE_RETRIES + 1):
                tmp_fd, tmp_path = tempfile.mkstemp(
                    prefix="stage_",
                    suffix=".tmp",
                    dir=cache_dir,
                )
                os.close(tmp_fd)

                try:
                    success = _copy_mounted_file(source_path, tmp_path)
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
                    else:
                        staged_size = (
                            os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
                        )
                        raise OSError(f"The staged file is too small ({staged_size} bytes)")
                except (OSError, shutil.Error) as error:
                    last_error = error
                    if os.path.exists(tmp_path):
                        try:
                            os.unlink(tmp_path)
                        except OSError:
                            pass

                    # Fallback: if previous cache exists, use it
                    if (
                        os.path.exists(cached_path)
                        and os.path.getsize(cached_path) >= FILE_STAGE_MIN_SIZE_BYTES
                    ):
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
                        time.sleep(FILE_STAGE_RETRY_DELAY_SECONDS)

            raise OSError(
                f"Unable to read '{filepath}' after {FILE_STAGE_RETRIES} attempts"
            ) from last_error

        finally:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
            except OSError:
                pass


@contextmanager
def stage_file_for_read(filepath: str, force_update: bool = False) -> Iterator[str]:
    """
    Context manager for reading staged files.
    Preserves the cached file on disk across calls.
    """
    staged_path = stage_file(filepath, force_update=force_update)
    yield staged_path
