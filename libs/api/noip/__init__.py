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

    def A(self, fqdn: str, content: str) -> dict:
        """
        Updates a type A record for the given hostname with the specified IP address.

        Args:
            hostname (str): The hostname to update.
            address (str): The new IP address to set.

        Returns:
            dict: The response from the NoIP API.
        """
        url = f"https://dynupdate.no-ip.com/nic/update"
        params = {
            "hostname": fqdn,
            "myip": content
        }
        try:
            response = requests.get(url, params=params, auth=(self.username, self.password))
            response.raise_for_status()
            __logger__.__logging__(f"Updated hostname '{fqdn}' to IP '{content}' successfully.", level=20)
            return {"status": "success", "response": response.text}
        except requests.exceptions.RequestException as e:
            __logger__.__logging__(f"Failed to update hostname '{fqdn}': {str(e)}", level=40)
            raise LoggedException(f"Error updating NoIP record: {str(e)}")
        
__logger__ = Logger(NoIP.integrate)
