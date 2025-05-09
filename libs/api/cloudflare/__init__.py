import json
import math
from typing import Literal, Optional, Self, TypeAlias
import requests
from libs.logger import LoggedException, logger
from libs.RecordsCache import RecordsCache

class Logger:
    def __init__(self, integrate: str):
        self.integrate = integrate
    def __logging__(self, message: any, level: int | str = 20, temporary_integrate: str = None):
        logger.log(level=level, msg=message, extra={"api": temporary_integrate if temporary_integrate else self.integrate})   
    def __verbose__(self, message: any, level: int | str = 10,  temporary_integrate: str = None):
        logger.log(level=level, msg=message, extra={"api": temporary_integrate if temporary_integrate else self.integrate})

class CloudFlare:
    """
    A class to interact with Cloudflare's API for managing DNS records.

    Attributes:
        integrate (str): Integration name for logging purposes.
        headers (dict): Authorization headers for API requests.
        cache (Optional[RecordsCache]): Cache for storing DNS records.
        cache_persistent (bool): Whether to persist cache data.
    """
    integrate = 'CloudFlare'
    
    def __init__(self: Self, email: str, password: str, cache_timeout: int = 86400, cache_persistent: bool = False):
        """
        Initialize the CloudFlare API client.

        Args:
            email (str): Cloudflare account email.
            password (str): API token for authentication.
            cache_timeout (int): Cache timeout in seconds. Use -1 for infinite timeout, 0 to disable caching.
            cache_persistent (bool): Whether to persist cache data to disk.
        """
        __logger__.__verbose__("Initializing CloudFlare API authorization...")
        
        self.headers = {
            "Content-Type": "application/json",
            "X-Auth-Email": email,
            "Authorization": f"Bearer {password}"
        }
        
        _ct = math.inf if cache_timeout.__le__(-1) else cache_timeout
        self.cache: Optional[type[RecordsCache]] = RecordsCache().build('cloudflare_records', timeout=_ct) if _ct.__ne__(0) else None
        self.cache_persistent = cache_persistent
    
    def getZoneId(self: Self, domain: str) -> str:
        """
        Retrieve the Zone ID for a given domain.

        Args:
            domain (str): The domain name to fetch the Zone ID for.

        Returns:
            str: The Zone ID of the domain.
        """
        url = "https://api.cloudflare.com/client/v4/zones"
        __logger__.__verbose__(f"Fetching zone id for domain: {domain}")

        response = requests.get(url, headers=self.headers, params={"name": domain})
        data = response.json()

        if not response.ok:
            LoggedException(self.integrate).exception(ConnectionError(f"Error fetching zone id for domain '{domain}'. Response Code: {response.status_code}, Error: {response.text}"))

        if data['success'] and data['result']:
            zone_id = data['result'][0]['id']
            __logger__.__verbose__(f"Zone ID retrieved for domain '{domain}': {zone_id}")
            return zone_id
        else:
            LoggedException(self.integrate).exception(ConnectionRefusedError("Domain not found or API call unsuccessful."))

    def getRecordId(self: Self, zone_id: str, record_name: str) -> str:
        """
        Retrieve the DNS record ID for a given record name in a specific zone.

        Args:
            zone_id (str): The Zone ID where the record is located.
            record_name (str): The name of the DNS record.

        Returns:
            str: The DNS record ID.
        """
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        __logger__.__verbose__(f"Fetching DNS record ID for record: {record_name} in zoneId: {zone_id}")

        response = requests.get(url, headers=self.headers, params={"name": record_name})
        data = response.json()

        if not response.ok:
            LoggedException(self.integrate).exception(ConnectionError(f"Error fetching DNS record ID for '{record_name}'. Response Code: {response.status_code}, Error: {response.text}"))

        if data['success'] and data['result']:
            record_id = data['result'][0]['id']
            __logger__.__verbose__(f"DNS record ID retrieved for record '{record_name}': {record_id}")
            return record_id
        else:
            LoggedException(self.integrate).exception(ConnectionRefusedError("DNS record not found or API call unsuccessful."))

    def getDNSRecord(self: Self, zone_id: str, filter: object = None) -> dict:
        """
        Fetch DNS records for a specific zone with optional filters.

        Args:
            zone_id (str): The Zone ID to fetch records from.
            filter (object, optional): Filters to apply when fetching records.

        Returns:
            dict: The DNS records matching the filter.
        """
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        __logger__.__verbose__(f"Fetching DNS records for zoneId: {zone_id} with filter: {filter}")

        response = requests.get(url, headers=self.headers, params=filter)
        response.raise_for_status()
        data = response.json()

        if not response.ok:
            LoggedException(self.integrate).exception(ConnectionError(f"Error fetching DNS records. Response Code: {response.status_code}, Error: {response.text}"))

        __logger__.__verbose__(f"DNS records retrieved: {data['result']}")
        return data['result']

    def __pokeCache__(self) -> None:
        """
        Verify and refresh the cache if necessary.
        """
        __logger__.__logging__("Verifying cache validity...")
        if self.cache_persistent:
            try:
                __logger__.__verbose__("Attempting to pull data from persistent cache...")
                self.cache.pull()
                __logger__.__verbose__("Data successfully pulled from cache.")

            except FileNotFoundError:
                __logger__.__verbose__("Failed to pull data from persistent cache. File not found.", 30)

        if self.cache.is_empty():
            __logger__.__verbose__("Cache is empty. Initializing a new self.cache...", 30)
        else:
            self.cache.__poke__()

    def __part_components__(self: Self, fqdn: str) -> dict:
        """
        Split a fully qualified domain name (FQDN) into its components.

        Args:
            fqdn (str): The fully qualified domain name.

        Returns:
            dict: A dictionary containing TLD, DN, and SDN components.
        """
        parts = fqdn.split('.')
        return {
            "TLD": parts[-1],
            "DN": parts[-2] if len(parts) > 1 else None,
            "SDN": ".".join(parts[:-2]) if len(parts) > 2 else None
        }
        
    def __cmit(self: Self, domain_type: str, zone_id: str, fqdn: str, dns_record_id: str) -> None:
        """
        Commit Zone ID and DNS record ID to the cache.

        Args:
            domain_type (str): The type of DNS record (e.g., A, AAAA).
            zone_id (str): The Zone ID.
            fqdn (str): The fully qualified domain name.
            dns_record_id (str): The DNS record ID.
        """
        # Cache the retrieved ZoneID and DNSRecordID if caching is enabled
        if not self.cache: return
        
        data = {
            "domain_type": domain_type,
            "zone_id": zone_id, "dns_record_id": dns_record_id
        }
        
        if not self.cache.is_exist(fqdn):
            self.cache.append(fqdn, data)
            __logger__.__verbose__(f"Appended cache with {data}.")
        elif self.cache.is_exist(fqdn) and not self.cache.is_valid(fqdn):
            self.cache.inject(fqdn, data)
            __logger__.__verbose__(f"Updated cache with {data}.")
        
        if self.cache_persistent:
            try:
                data = self.cache.read()
                
                if not self.cache.is_same(data):
                    self.cache.commit()
                    __logger__.__verbose__("Committed cache to Persistent Cache.")
                else: __logger__.__verbose__("No changes needed for Persistent Cache is is already up-to-date.")
            except FileNotFoundError:
                self.cache.commit()
                __logger__.__verbose__("Committed cache to Persistent Cache.")
    
    def A(self: Self, fqdn: str, content: str, ttl: int = None, proxied: bool = None, comment: str = None) -> None:
        """
        Update an A record in Cloudflare's DNS.

        Args:
            fqdn (str): The fully qualified domain name.
            content (str): The IPv4 address for the A record.
            ttl (int, optional): Time-to-live for the record in seconds.
            proxied (bool, optional): Whether the record is proxied through Cloudflare.
            comment (str, optional): A comment for the record.
        """
        domain_type = "A"
        if self.cache: self.__pokeCache__()

        # Split FQDN into components
        __logger__.__verbose__(f"Processing A record update for FQDN: {fqdn}, Content: {content}")
        fqdn_split = self.__part_components__(fqdn)
        __logger__.__verbose__(f"FQDN split into TLD: {fqdn_split['TLD']}, DN: {fqdn_split['DN']}, SDN: {fqdn_split['SDN']}")

        domain = f"{fqdn_split['DN']}.{fqdn_split['TLD']}"
        __logger__.__verbose__(f"Determined domain: {domain}")
        
        cache = None if not (self.cache and self.cache.is_exist(fqdn)) else self.cache.get(fqdn)

        zone_id = self.getZoneId(domain) if not cache else cache["zone_id"]
        dns_record_id = self.getRecordId(zone_id, fqdn) if not cache else cache["dns_record_id"]
        old_record: dict = self.getDNSRecord(zone_id, {"name": fqdn})
        if not old_record:
            LoggedException(self.integrate).exception(self.integrate).exception(KeyError(f"No domain name '{fqdn}' found in your DNS records. Please create it first."))

        # Cache the retrieved ZoneID and DNSRecordID if caching is enabled
        self.__cmit(domain_type, zone_id, fqdn, dns_record_id)           
        
        # Check if the content is already up-to-date
        if content == old_record[0]['content']:
            return __logger__.__logging__(f"No changes needed for '{fqdn}', content is already up-to-date.")

        # Prepare data for the DNS record update
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}"
        data = {
            "type": domain_type,
            "name": fqdn,
            "content": content,
            "ttl": ttl if ttl is not None else old_record[0]['ttl'],
            "proxied": proxied if proxied is not None else old_record[0]['proxied'],
            "comment": comment if comment is not None else old_record[0].get('comment', "")
        }

        # Send the update request
        __logger__.__verbose__(f"Updating DNS record with data: {data}")
        response = requests.put(url, headers=self.headers, json=data)
        result = response.json()

        # Handle response errors
        if not response.ok:
            LoggedException(self.integrate).exception(ConnectionError(f"Error updating DNS record. Response Code: {response.status_code}, Error: {response.text}"))

        if not result.get("success", False):
            LoggedException(self.integrate).exception(ConnectionRefusedError(f"Failed to update content of '{fqdn}' to '{content}'. Errors: {result['errors']}"))

        __logger__.__logging__(f"Successfully updated DNS record for '{fqdn}' with new content: {content}")

    def AAAA(self: Self, fqdn: str, content: str, ttl: int = None, proxied: bool = None, comment: str = None) -> None:
        """
        Update an AAAA record in Cloudflare's DNS.

        Args:
            fqdn (str): The fully qualified domain name.
            content (str): The IPv6 address for the AAAA record.
            ttl (int, optional): Time-to-live for the record in seconds.
            proxied (bool, optional): Whether the record is proxied through Cloudflare.
            comment (str, optional): A comment for the record.
        """
        domain_type = "AAAA"
        if self.cache_persistent: self.__pokeCache__()
        
        # Split FQDN into components
        __logger__.__verbose__(f"Processing A record update for FQDN: {fqdn}, Content: {content}")
        fqdn_split = self.__part_components__(fqdn)
        __logger__.__verbose__(f"FQDN split into TLD: {fqdn_split['TLD']}, DN: {fqdn_split['DN']}, SDN: {fqdn_split['SDN']}")

        domain = f"{fqdn_split['DN']}.{fqdn_split['TLD']}"
        __logger__.__verbose__(f"Determined domain: {domain}")
        
        cache = None if not (self.cache and self.cache.is_exist(fqdn)) else self.cache.get(fqdn)

        zone_id = self.getZoneId(domain) if not cache else cache["zone_id"]
        dns_record_id = self.getRecordId(zone_id, fqdn) if not cache else cache["dns_record_id"]
        old_record: dict = self.getDNSRecord(zone_id, {"name": fqdn})
        if not old_record:
            LoggedException(self.integrate).exception(KeyError(f"No domain name '{fqdn}' found in your DNS records. Please create it first."))

        self.__cmit(domain_type, zone_id, fqdn, dns_record_id)
        
        # Check if the content is already up-to-date
        if content == old_record[0]['content']:
            return __logger__.__logging__(f"No changes needed for '{fqdn}', content is already up-to-date.")

        # Prepare data for the DNS record update
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}"
        data = {
            "type": domain_type,
            "name": fqdn,
            "content": content,
            "ttl": ttl if ttl is not None else old_record[0]['ttl'],
            "proxied": proxied if proxied is not None else old_record[0]['proxied'],
            "comment": comment if comment is not None else old_record[0].get('comment', "")
        }

        # Send the update request
        __logger__.__verbose__(f"Updating DNS record with data: {data}")
        response = requests.put(url, headers=self.headers, json=data)
        result = response.json()

        # Handle response errors
        if not response.ok:
            LoggedException(self.integrate).exception(ConnectionError(f"Error updating DNS record. Response Code: {response.status_code}, Error: {response.text}"))

        if not result.get("success", False):
            LoggedException(self.integrate).exception(ConnectionRefusedError(f"Failed to update content of '{fqdn}' to '{content}'. Errors: {result['errors']}"))

        __logger__.__logging__(f"Successfully updated DNS record for '{fqdn}' with new content: {content}")

__logger__ = Logger(CloudFlare.integrate)
