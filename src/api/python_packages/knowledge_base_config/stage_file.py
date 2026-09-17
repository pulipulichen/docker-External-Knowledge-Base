import logging
import os
import shutil
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


@contextmanager
def stage_file_for_read(filepath: str) -> Iterator[str]:
    """Copy a local or mounted file to a local temporary file before parsing it."""

    if not filepath:
        raise FileNotFoundError("No file path was configured")

    source_path = os.path.realpath(filepath) if os.path.islink(filepath) else filepath
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"File not found: {filepath}")
    if os.path.isdir(source_path):
        raise IsADirectoryError(f"Expected a file, got directory: {filepath}")

    suffix = os.path.splitext(source_path)[1]
    staged_path = None
    last_error = None

    try:
        for attempt in range(1, FILE_STAGE_RETRIES + 1):
            fd, candidate_path = tempfile.mkstemp(
                prefix="knowledge-base-",
                suffix=suffix,
                dir="/tmp",
            )
            try:
                with os.fdopen(fd, "wb") as destination:
                    with open(source_path, "rb") as source:
                        shutil.copyfileobj(source, destination, length=1024 * 1024)
                    destination.flush()
                    os.fsync(destination.fileno())

                staged_size = os.path.getsize(candidate_path)
                if staged_size < FILE_STAGE_MIN_SIZE_BYTES:
                    raise OSError(
                        f"The staged file is too small ({staged_size} bytes)"
                    )

                staged_path = candidate_path
                logger.info(
                    "Staged file '%s' for reading at '%s' on attempt %d",
                    filepath,
                    staged_path,
                    attempt,
                )
                break
            except (OSError, shutil.Error) as error:
                last_error = error
                try:
                    os.unlink(candidate_path)
                except OSError:
                    pass

                logger.warning(
                    "Unable to stage file '%s' on attempt %d/%d: %s",
                    filepath,
                    attempt,
                    FILE_STAGE_RETRIES,
                    error,
                )
                if attempt < FILE_STAGE_RETRIES:
                    time.sleep(FILE_STAGE_RETRY_DELAY_SECONDS)

        if staged_path is None:
            raise OSError(
                f"Unable to read '{filepath}' after {FILE_STAGE_RETRIES} attempts"
            ) from last_error

        # Closing the source before parsing prevents later reads from touching
        # the remote mount.
        yield staged_path
    finally:
        if staged_path:
            try:
                os.unlink(staged_path)
            except OSError:
                logger.debug("Unable to remove staged file '%s'", staged_path)
