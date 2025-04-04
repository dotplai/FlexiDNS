import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Self, Union

class LoggedException(Exception):
    def __init__(self, api=None) -> Self:
        self.api = api

    def exception(self, message: Union[any, Exception]) -> None:
        logger.exception(message, extra={"api": self.api})
        super().__init__(message)

log_format = logging.Formatter(
    "%(asctime)s | %(name)s %(levelname)s::%(api)s: %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)

log_directory = 'logs'
os.makedirs(log_directory, exist_ok=True)

log_file = os.path.join(log_directory, 'flexidns.log')
debug_file = os.path.join(log_directory, 'flexidns_debug.log')


logger = logging.getLogger("FlexiDNS")
logger.setLevel(logging.DEBUG)  # Set to the lowest level for capturing all logs

# Handler for INFO and higher levels (info.log)
info_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
info_handler.setLevel(logging.INFO)  # Only log INFO and higher levels to this handler
info_handler.setFormatter(log_format)
logger.addHandler(info_handler)

# Handler for DEBUG and higher levels (debug.log)
debug_handler = RotatingFileHandler(debug_file, maxBytes=5 * 1024 * 1024, backupCount=5)
debug_handler.setLevel(logging.DEBUG)  # Log DEBUG and higher levels to this handler
debug_handler.setFormatter(log_format)
logger.addHandler(debug_handler)

# Console handler for INFO and higher levels
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Only log INFO and higher levels to the console
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

