import logging
from constants.constants import LOGGING_CONFIG

def configure_logging():
	logging.basicConfig(
		filename=LOGGING_CONFIG["LOG_FILE"],
		level=getattr(logging, LOGGING_CONFIG["LOG_LEVEL"].upper()),
		format="%(asctime)s - %(levelname)s - %(message)s",
	)