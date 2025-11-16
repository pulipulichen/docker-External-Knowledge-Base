import logging
import requests
import os
import datetime

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # Changed to DEBUG for debugging

def download_file(knowledge_id):
    config = get_knowledge_base_config(knowledge_id)

    if 'path' in config:
        # logger.info(f"Retrieved URL for knowledge_id '{knowledge_id}': {config.get('path')}")
        # Further ingestion logic using the URL would go here

        downloaded_file_path = config.get('file_path')
        
        update_delay_seconds = config.get('update_delay_seconds', 30 * 60)
        # logger.debug(f"Expiration seconds: {update_delay_seconds}")

        # If downloaded_file_path exists and its modification time is less than expiration_seconds, do not re-download
        if os.path.exists(downloaded_file_path):
            if update_delay_seconds == -1:
                # logger.info("update_delay_seconds is -1 and file already exists. Skipping download.")
                return False

            file_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(downloaded_file_path))
            current_time = datetime.datetime.now()
            time_difference = current_time - file_mod_time
            
            # logger.debug(f"File modification time: {file_mod_time}")
            # logger.debug(f"Current time: {current_time}")
            # logger.debug(f"Time difference: {time_difference}")
            # logger.debug(f"Expiration timedelta: {datetime.timedelta(seconds=expiration_seconds)}")

            if time_difference < datetime.timedelta(seconds=update_delay_seconds):
                logger.info("File is up to date. Skipping download.")
                return False
        
        file_url = config.get('path')
        if file_url.startswith('http://') or file_url.startswith('https://'):
            logger.info("URL is a valid HTTP/HTTPS URL.")
            
            response = requests.get(file_url)
            
            with open(downloaded_file_path, 'wb') as f:
                f.write(response.content)
            
            os.chmod(downloaded_file_path, 0o777)

            if downloaded_file_path:
                logger.info(f"Ingestion successful for knowledge_id '{knowledge_id}'. File saved at: {downloaded_file_path}")
            else:
                logger.error(f"Ingestion failed for knowledge_id '{knowledge_id}'.")

            return True

    # ==============================

    return False
