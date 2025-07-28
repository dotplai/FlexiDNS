import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Self, Union, Any
import traceback
from configparser import ConfigParser

def parse(val: str) -> Union[bool, int, float, str]:
    val = val.strip()
    val_lower = val.lower()
    if val_lower == 'true':
        return True
    if val_lower == 'false':
        return False
    try:
        return float(val) if '.' in val else int(val)
    except ValueError:
        return val

class Logger:
    def __init__(self, integrate: str):
        self.integrate = integrate
    
    def log(self, message: Any, level: int = logging.INFO) -> None:
        logger.log(level=level, msg=message, extra={"api": self.integrate})

    def verbose(self, message: Any, level: int = logging.DEBUG) -> None:
        self.log(message, level)

    def exception(self, e: Exception) -> None:
        self.log(f"ERROR::{self.integrate}: {str(e)}\n{traceback.format_exc()}", logging.ERROR)

def setup_handler(handler, level_includes, level_map):
    for level_name, level in level_map.items():
        if level_name in level_includes:
            handler.setLevel(level)
            break
    return handler

def init_logging():
    config = ConfigParser(allow_no_value=False, default_section='General')
    config.read('config.ini')
    
    enabled = config.getboolean('Logging', 'enabledFile')
    log_include = config.get('Logging', 'logIncluded').strip('",[] ').replace(' ', '').split(',')
    console_include = config.get('Logging', 'consoleIncluded').strip('",[] ').replace(' ', '').split(',')

    logger = logging.getLogger("FlexiDNS")
    logger.setLevel(logging.DEBUG)

    log_format = logging.Formatter(
        "%(asctime)s | %(name)s %(levelname)s::%(api)s: %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    level_map = {
        'debug': logging.DEBUG,
        'normal': logging.INFO,
        'error': logging.ERROR
    }

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler = setup_handler(console_handler, console_include, level_map)
    logger.addHandler(console_handler)

    if enabled:
        log_directory = 'logs'
        os.makedirs(log_directory, exist_ok=True)
        
        if config.getboolean('Logging', 'splitLogs', fallback=True):
            for level_name, level in level_map.items():
                if level_name in log_include:
                    handler = RotatingFileHandler(
                        os.path.join(log_directory, f'flexidns.{level_name}.log') if level_name != 'normal' else os.path.join(log_directory, 'flexidns.log'),

                        maxBytes=5 * 1024 * 1024,
                        backupCount=5
                    )
                    handler.setLevel(level)
                    handler.setFormatter(log_format)
                    logger.addHandler(handler)
        else:
            base_handler = RotatingFileHandler(
                os.path.join(log_directory, 'flexidns.log'),
                maxBytes=5 * 1024 * 1024,
                backupCount=5
            )
            base_handler.setFormatter(log_format)
            base_handler = setup_handler(base_handler, log_include, level_map)
            logger.addHandler(base_handler)

    return logger

logger = init_logging()