from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

config = {
    "output_format": "markdown",
    "ADDITIONAL_KEY": "VALUE"
}
config_parser = ConfigParser(config)

converter = PdfConverter(
    config=config_parser.generate_config_dict(),
    artifact_dict=create_model_dict(),
    processor_list=config_parser.get_processors(),
    renderer=config_parser.get_renderer(),
    llm_service=config_parser.get_llm_service()
)

def convert_file_path_to_markdown_content(file_path):
    rendered = converter(file_path)

    logger.info("rendered: %s", rendered)

    return rendered