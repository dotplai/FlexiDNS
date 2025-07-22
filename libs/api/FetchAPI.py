import json
import os
import requests
from datetime import datetime
from typing import Any, Union, Optional

# This module provides a simple interface to fetch public IP address and other network information from ifconfig.me ----- ifconfig.me
class ifconfig:
    def __init__(self, path: str = 'all.json') -> None:
        self.api_uri = f'https://ifconfig.me/{path}'
        self.dumps = "dumps/"
    def get(self, format: Optional[str] = None) -> Union[dict, str]:
        """Fetch data from ifconfig.me"""
        if self.api_uri.endswith('.json') and format is None: format = 'json'
        else: format = 'text'

        __address__ = f"{self.api_uri}?format={format}" if format else self.api_uri
        res = requests.get(__address__)
        res.raise_for_status()
        if not res.ok:
            raise ConnectionError(f"Response error: {res.status_code} - {res.reason}")
        
        # --- Save Response to response.json (Beautified) ---
        ifinfo = res.json() if format in ('json', 'jsonp') else res.text
        if format in ('json', 'jsonp'):
            os.makedirs(self.dumps, exist_ok=True)  # Ensure directory exists
            with open(f"{self.dumps}ifconfig@{datetime.now().strftime('%d-%m-%Y:%H-%M-%S')}.jsonc", "w") as f:
                json.dump(ifinfo, f, indent=4)

            print("✅ Dumped response to 'ifconfig.jsonc'")

        return ifinfo

# This module provides a simple interface to fetch public IP address from ipify.org ----- ipify.org
class ipify:
    def __init__(self, internet_protocol_verison: int = 4):
        self.api_uri = f'https://api{internet_protocol_verison}.ipify.org'
          
    def get_address(self, format: str = 'json', callback: Optional[str] = None) -> Union[dict, str, Any, requests.Response]:
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
    def get_ipv4(format: str = 'json', callback: Optional[str] = None) -> Union[dict, str, Any, requests.Response]:
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
    def get_ipv6(format: str = 'json', callback: Optional[str] = None) -> Union[dict, str, Any, requests.Response]:
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
    def get_ipv64(format: str = 'json', callback: Optional[str] = None) -> Union[dict, str, Any, requests.Response]:
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
