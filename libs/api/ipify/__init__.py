import requests
from typing import Union

class ipify:
    def __init__(self, internet_protocol_verison: int = 4):
        self.api_uri = f'https://api{internet_protocol_verison}.ipify.org'
          
    def get_address(self, format: str = 'json', callback: str = None) -> Union[dict, str, any, requests.Response]:
        __address__ = (
            f"{self.api_uri}"
            f"{'?format=' + format if format else ''}"
            f"{'&callback=' + callback if callback else ''}"
        )

        res = requests.get(__address__)
        res.raise_for_status()
        if not res.ok:
            raise ConnectionError(f"Response error: {res.status_code} - {res.reason}")
        
        return res.json if format in ('json' or 'jsonp') else res.text

    @staticmethod
    def get_ipv4(format: str = 'json', callback: str = None) -> Union[dict, str, any, requests.Response]:
        __address__ = (
            "https://api4.ipify.org"
            f"{'?format=' + format if format else ''}"
            f"{'&callback=' + callback if callback else ''}"
        )

        res = requests.get(__address__)
        res.raise_for_status()
        if not res.ok:
            raise ConnectionError(f"Response error: {res.status_code} - {res.reason}")
        return res.json if format in ('json' or 'jsonp') else res.text
    
    @staticmethod
    def get_ipv6(format: str = 'json', callback: str = None) -> Union[dict, str, any, requests.Response]:
        __address__ = (
            "https://api6.ipify.org"
            f"{'?format=' + format if format else ''}"
            f"{'&callback=' + callback if callback else ''}"
        )

        res = requests.get(__address__)
        res.raise_for_status()
        if not res.ok:
            raise ConnectionError(f"Response error: {res.status_code} - {res.reason}")
        return res.json if format in ('json' or 'jsonp') else res.text
    
    @staticmethod
    def get_ipv64(format: str = 'json', callback: str = None) -> Union[dict, str, any, requests.Response]:
        __address__ = (
            "https://api64.ipify.org"
            f"{'?format=' + format if format else ''}"
            f"{'&callback=' + callback if callback else ''}"
        )

        res = requests.get(__address__)
        res.raise_for_status()
        if not res.ok:
            raise ConnectionError(f"Response error: {res.status_code} - {res.reason}")
        return res.json if format in ('json' or 'jsonp') else res.text
