import logging

from .log_config import setup_logger

setup_logger(enable_file=True)
logger = logging.getLogger(__name__)
