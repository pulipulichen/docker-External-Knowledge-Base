import datetime
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

INDEX_LOCK_DIR = "/tmp/docker-External-Knowledge-Base-lock/"
INDEX_LOCK_MAX_AGE = datetime.timedelta(minutes=30)

def get_lock_filepath(knowledge_id):
    os.makedirs(INDEX_LOCK_DIR, exist_ok=True)
    lock_filepath = INDEX_LOCK_DIR + knowledge_id + ".lock.txt"

    return lock_filepath


def lock_index(knowledge_id):
    lock_filepath = get_lock_filepath(knowledge_id)

    if os.path.exists(lock_filepath):
        try:
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(lock_filepath))
            if datetime.datetime.now() - mtime <= INDEX_LOCK_MAX_AGE:
                return False
            os.remove(lock_filepath)
            logger.info(
                "Removed stale index lock (older than %s): %s",
                INDEX_LOCK_MAX_AGE,
                lock_filepath,
            )
        except OSError as e:
            logger.error("Failed to check or remove stale lock file %s: %s", lock_filepath, e)
            return False

    try:
        with open(lock_filepath, "w") as f:
            f.write(datetime.datetime.now().isoformat())
        return True
    except Exception as e:
        logger.error(f"Failed to create lock file {lock_filepath}: {e}")
        return False


def unlock_index(knowledge_id):
    lock_filepath = get_lock_filepath(knowledge_id)

    if os.path.exists(lock_filepath):
        try:
            os.remove(lock_filepath)
            return True
        except Exception as e:
            logger.error(f"Failed to remove lock file {lock_filepath}: {e}")
            return False
    return False
