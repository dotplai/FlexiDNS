import json
from typing import Literal, Self, TypeAlias
import requests
from libs.logging import Logger

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
        url = "https://dynupdate.no-ip.com/nic/update"
        params = {
            "hostname": fqdn,
            "myip": content
        }
        try:
            response = requests.get(url, params=params, auth=(self.username, self.password))
            response.raise_for_status()
            logger.__logging__(f"Updated hostname '{fqdn}' to IP '{content}' successfully.", level=20)
            return {"status": "success", "response": response.text}
        except requests.exceptions.RequestException as e:
            logger.__logging__(f"Failed to update hostname '{fqdn}': {str(e)}", level=40)
            raise logger.exception(f"Error updating NoIP record: {str(e)}")
        
logger = Logger(NoIP.integrate)
