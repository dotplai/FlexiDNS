import json
from typing import Literal, Self, TypeAlias
import requests
from libs.logger import LoggedException, logger

class Logger:
    def __init__(self, integrate: str):
        self.integrate = integrate
    def __logging__(self, message: any, level: int | str = 20, temporary_integrate: str = None):
        logger.log(level=level, msg=message, extra={"api": temporary_integrate if temporary_integrate else self.integrate})   
    def __verbose__(self, message: any, level: int | str = 10,  temporary_integrate: str = None):
        logger.log(level=level, msg=message, extra={"api": temporary_integrate if temporary_integrate else self.integrate})

class NoIP:
    integrate = 'NoIP'
    
    def __init__(self: Self, username: str, password: str):
        self.username = username
        self.password = password
        
    def A(self: Self, fqdn: str, content: str, overHTTPS: bool = True): pass
        
__logger__ = Logger(NoIP.integrate)
