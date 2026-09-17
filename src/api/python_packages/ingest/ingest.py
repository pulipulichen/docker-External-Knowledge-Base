
import logging
import os

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config
from ..knowledge_base_config.get_section_name import get_section_name
from ..knowledge_base_config.stage_file import stage_file, is_mounted_or_symlink

from .download_file import download_file
from .convert_file_to_markdown import convert_file_to_markdown
from .convert_dir_to_markdown import convert_dir_to_markdown
from ..index.index_file import index_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# import time

def _is_spreadsheet(path: str | None) -> bool:
    return bool(path) and os.path.splitext(path)[1].lower() in {".ods", ".xlsx"}


def _stage_mounted_spreadsheet(config: dict, force_update: bool = False) -> bool:
    """Pre-stage mounted spreadsheets into local persistent cache before indexing."""

    filepath = config.get("file_path")
    if not _is_spreadsheet(filepath) or not is_mounted_or_symlink(filepath):
        return True

    try:
        stage_file(
            filepath,
            force_update=force_update,
            rclone_source=config.get("rclone_source"),
        )
        return True
    except (OSError, ValueError) as error:
        logger.error(
            "Unable to read mounted spreadsheet '%s'; skipping ingest: %s",
            filepath,
            error,
        )
        return False


async def ingest_data(knowledge_id, section_name, force_update: False):
    # time.sleep(30)

    logger.info(f"Knowledge ID: {knowledge_id}")
    # logger.info(f"force_update: {force_update}")

    knowledge_base_config = get_knowledge_base_config(knowledge_id)

    if not _stage_mounted_spreadsheet(knowledge_base_config, force_update):
        return False

    # logger.info(f"knowledge_base_config: {knowledge_base_config}")

    if knowledge_base_config.get('is_url') is True:
        download_file(knowledge_id, force_update)
    elif knowledge_base_config.get('markdown_convertable') is True:
        convert_file_to_markdown(knowledge_id, force_update)
    # elif knowledge_base_config.get('is_file') is False:
    #     convert_dir_to_markdown(knowledge_id, force_update)

    if section_name is None:
        section_name = get_section_name(knowledge_id)

    logger.info(f"section_name: {section_name}")

    await index_file(knowledge_id, section_name, force_update)
