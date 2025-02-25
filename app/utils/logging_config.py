import logging
from constants.constants import LOGGING_CONFIG

def configure_logging():
	logging.basicConfig(
		filename="bot.log",
		level=logging.INFO,
		format="%(asctime)s - %(levelname)s - %(message)s",
	)
	# Add a console handler to see logs in the terminal
	console_handler = logging.StreamHandler()
	console_handler.setLevel(logging.INFO)
	formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
	console_handler.setFormatter(formatter)
	logging.getLogger().addHandler(console_handler)