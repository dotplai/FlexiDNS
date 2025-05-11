import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Self, Union

class Logger:
    def __init__(self, integrate: str):
        self.integrate = integrate

    def set_integrate(self, integrate: str) -> Self:
        self.integrate = integrate
        return self
    
    def log(self, message: any, level: int | str = 20) -> None:
        logger.log(level=level, msg=message, extra={"api": self.integrate})

    def verbose(self, message: any, level: int | str = 10) -> None:
        logger.log(level=level, msg=message, extra={"api": self.integrate})

    def exception(self, message: Union[any, Exception]) -> None:
        logger.exception(message, extra={"api": self.integrate})
        super().__init__(message)


logger = logging.getLogger("FlexiDNS")
logger.setLevel(logging.DEBUG)

log_format = logging.Formatter(
    "%(asctime)s | %(name)s %(levelname)s::%(api)s: %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Console handler (always active)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

# Attempt to add file handlers
log_directory = 'logs'
log_file = os.path.join(log_directory, 'flexidns.log')
debug_file = os.path.join(log_directory, 'flexidns_debug.log')

try:
    os.makedirs(log_directory, exist_ok=True)
    test_file = os.path.join(log_directory, '.write_test')
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)

    info_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(log_format)
    logger.addHandler(info_handler)

    debug_handler = RotatingFileHandler(debug_file, maxBytes=5 * 1024 * 1024, backupCount=5)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(log_format)
    logger.addHandler(debug_handler)

except Exception:
    logger.warning("⚠️ Log directory not writable - logging to terminal only.")
