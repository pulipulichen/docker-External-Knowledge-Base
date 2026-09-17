import hashlib
import logging
import os
import shutil
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


def stage_file(filepath: str, force_update: bool = False) -> str:
    """
    Ensure a mounted or symlinked file is copied to a persistent local cache.

    If the source file cannot be read (e.g. rclone Input/output error) but a
    previous cache exists, it falls back to the existing cache with a warning.
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

    # If cache exists and is not forced to update, check freshness
    if os.path.exists(cached_path) and os.path.getsize(cached_path) >= FILE_STAGE_MIN_SIZE_BYTES:
        if not force_update:
            try:
                source_mtime = os.path.getmtime(source_path)
                cached_mtime = os.path.getmtime(cached_path)
                if cached_mtime >= source_mtime:
                    logger.debug("Staged file cache is up-to-date: '%s'", cached_path)
                    return cached_path
            except OSError:
                logger.debug("Using existing cache for '%s' without mtime check", filepath)
                return cached_path

    last_error = None
    tmp_path = f"{cached_path}.{os.getpid()}.tmp"

    for attempt in range(1, FILE_STAGE_RETRIES + 1):
        try:
            with open(source_path, "rb") as source, open(tmp_path, "wb") as destination:
                shutil.copyfileobj(source, destination, length=1024 * 1024)
                destination.flush()
                os.fsync(destination.fileno())

            staged_size = os.path.getsize(tmp_path)
            if staged_size < FILE_STAGE_MIN_SIZE_BYTES:
                raise OSError(f"The staged file is too small ({staged_size} bytes)")

            try:
                source_mtime = os.path.getmtime(source_path)
                os.utime(tmp_path, (source_mtime, source_mtime))
            except OSError:
                pass

            os.replace(tmp_path, cached_path)
            logger.info(
                "Staged file '%s' for reading at '%s' on attempt %d",
                filepath,
                cached_path,
                attempt,
            )
            return cached_path
        except (OSError, shutil.Error) as error:
            last_error = error
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

            # Graceful fallback: if a previous cache exists, use it instead of failing
            if os.path.exists(cached_path) and os.path.getsize(cached_path) >= FILE_STAGE_MIN_SIZE_BYTES:
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


@contextmanager
def stage_file_for_read(filepath: str, force_update: bool = False) -> Iterator[str]:
    """
    Context manager for reading staged files.
    Preserves the cached file on disk across calls.
    """
    staged_path = stage_file(filepath, force_update=force_update)
    yield staged_path
