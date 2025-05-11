import json
from typing import Literal, Self, TypeAlias
import requests
from libs.logging import Logger

class DynDNS:
    integrate = 'DynDNS'
    
    def __init__(self: Self, username: str, password: str):
        self.username = username
        self.password = password
        
logger = Logger(DynDNS.integrate)
