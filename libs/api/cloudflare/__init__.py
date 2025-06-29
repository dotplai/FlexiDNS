import json
import math
from typing import Any, Literal, Optional, Self, TypeAlias, Union
import requests
from libs.logging import Logger
from libs.RecordsCache import RecordsCache


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
        logger.verbose("Initializing CloudFlare API authorization...")
        
        self.headers = {
            "Content-Type": "application/json",
            "X-Auth-Email": email,
            "Authorization": f"Bearer {password}"
        }
        
        _ct = int(1e18) if cache_timeout <= -1 else int(cache_timeout)
        self.cache: Optional[RecordsCache] = RecordsCache().build('cloudflare_records', timeout=_ct) if _ct != 0 else None
        self.cache_persistent = cache_persistent
    
    def get_zone_id(self: Self, domain: str) -> str:
        """
        Retrieve the Zone ID for a given domain.

        Args:
            domain (str): The domain name to fetch the Zone ID for.

        Returns:
            str: The Zone ID of the domain.
        """
        url = "https://api.cloudflare.com/client/v4/zones"
        logger.verbose(f"Fetching zone id for domain: {domain}")

        response = requests.get(url, headers=self.headers, params={"name": domain})
        data = response.json()

        if not response.ok:
            raise ConnectionError(f"Error fetching zone id for domain '{domain}'. Response Code: {response.status_code}, Error: {response.text}")

        if data['success'] and data['result']:
            zone_id = data['result'][0]['id']
            logger.verbose(f"Zone ID retrieved for domain '{domain}': {zone_id}")
            return zone_id
        else:
            raise ConnectionRefusedError(f"DNS record not found or API call unsuccessful.\n*** Success: {data['success']} | Result: {data['result']}")

    def get_record_id(self: Self, zone_id: str, record_name: str) -> str:
        """
        Retrieve the DNS record ID for a given record name in a specific zone.

        Args:
            zone_id (str): The Zone ID where the record is located.
            record_name (str): The name of the DNS record.

        Returns:
            str: The DNS record ID.
        """
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        logger.verbose(f"Fetching DNS record ID for record: {record_name} in zoneId: {zone_id}")

        response = requests.get(url, headers=self.headers, params={"name": record_name})
        data = response.json()

        if not response.ok:
            raise ConnectionError(f"Error fetching DNS record ID for '{record_name}'. Response Code: {response.status_code}, Error: {response.text}")

        if data['success'] and data['result']:
            record_id = data['result'][0]['id']
            logger.verbose(f"DNS record ID retrieved for record '{record_name}': {record_id}")
            return record_id
        else:
            raise ConnectionRefusedError("DNS record not found or API call unsuccessful.")

    def get_dns_records(self: Self, zone_id: str, filter: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        """
        Fetch DNS records for a specific zone with optional filters.

        Args:
            zone_id (str): The Zone ID to fetch records from.
            filter (dict[str, any], optional): Filters to apply when fetching records.

        Returns:
            dict: The DNS records matching the filter.
        """
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        logger.verbose(f"Fetching DNS records for zoneId: {zone_id} with filter: {filter}")

        response = requests.get(url, headers=self.headers, params=filter)
        response.raise_for_status()
        data = response.json()

        if not response.ok:
            logger.exception(ConnectionError(f"Error fetching DNS records. Response Code: {response.status_code}, Error: {response.text}"))

        logger.verbose(f"DNS records retrieved: {data['result']}")
        return data['result']

    def __poke_cache__(self) -> None:
        """
        Verify and refresh the cache if necessary.
        """
        logger.log("Verifying cache validity...")
        if self.cache_persistent:
            try:
                logger.verbose("Attempting to pull data from persistent cache...")
                if self.cache is not None:
                    self.cache.pull()
                    logger.verbose("Data successfully pulled from cache.")

            except FileNotFoundError:
                logger.verbose("Failed to pull data from persistent cache. File not found.", 30)

        if self.cache is not None and self.cache.is_empty():
            logger.verbose("Cache is empty. Initializing a new self.cache...", 30)
        elif self.cache is not None:
            self.cache.poke()

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
            logger.verbose(f"Appended cache with {data}.")
        elif self.cache.is_exist(fqdn) and not self.cache.is_valid(fqdn):
            self.cache.inject(fqdn, data)
            logger.verbose(f"Updated cache with {data}.")
        
        if self.cache_persistent:
            try:
                data = self.cache.read()
                
                if not self.cache.is_same(data):
                    self.cache.commit()
                    logger.verbose("Committed cache to Persistent Cache.")
                else: logger.verbose("No changes needed for Persistent Cache is is already up-to-date.")
            except FileNotFoundError:
                self.cache.commit()
                logger.verbose("Committed cache to Persistent Cache.")
    
    def A(self: Self, fqdn: str, content: str, ttl: Optional[int] = None, proxied: Optional[bool] = None, comment: Optional[str] = None) -> None:
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
        if self.cache: self.__poke_cache__()

        # Split FQDN into components
        logger.verbose(f"Processing A record update for FQDN: {fqdn}, Content: {content}")
        fqdn_split = self.__part_components__(fqdn)
        logger.verbose(f"FQDN split into TLD: {fqdn_split['TLD']}, DN: {fqdn_split['DN']}, SDN: {fqdn_split['SDN']}")

        domain = f"{fqdn_split['DN']}.{fqdn_split['TLD']}"
        logger.verbose(f"Determined domain: {domain}")
        
        cache = None if not (self.cache and self.cache.is_exist(fqdn)) else self.cache.get(fqdn)

        zone_id = self.get_zone_id(domain) if not cache else cache["zone_id"]
        dns_record_id = self.get_record_id(zone_id, fqdn) if not cache else cache["dns_record_id"]
        old_record: list[dict[str, Any]] = self.get_dns_records(zone_id, {"name": fqdn})
        if not old_record:
            raise KeyError(f"No domain name '{fqdn}' found in your DNS records. Please create it first.")

        # Cache the retrieved ZoneID and DNSRecordID if caching is enabled
        self.__cmit(domain_type, zone_id, fqdn, dns_record_id)           
        
        # Check if the content is already up-to-date
        if content == old_record[0]['content']:
            return logger.log(f"No changes needed for '{fqdn}', content is already up-to-date.")

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
        logger.verbose(f"Updating DNS record with data: {data}")
        response = requests.put(url, headers=self.headers, json=data)
        result = response.json()

        # Handle response errors
        if not response.ok:
            raise ConnectionError(f"Error updating DNS record. Response Code: {response.status_code}, Error: {response.text}")

        if not result.get("success", False):
            raise ConnectionRefusedError(f"Failed to update content of '{fqdn}' to '{content}'. Errors: {result['errors']}")

        logger.log(f"Successfully updated DNS record for '{fqdn}' with new content: {content}")

    def AAAA(self: Self, fqdn: str, content: str, ttl: Optional[int] = None, proxied: Optional[bool] = None, comment: Optional[str] = None) -> None:
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
        if self.cache_persistent: self.__poke_cache__()
        
        # Split FQDN into components
        logger.verbose(f"Processing A record update for FQDN: {fqdn}, Content: {content}")
        fqdn_split = self.__part_components__(fqdn)
        logger.verbose(f"FQDN split into TLD: {fqdn_split['TLD']}, DN: {fqdn_split['DN']}, SDN: {fqdn_split['SDN']}")

        domain = f"{fqdn_split['DN']}.{fqdn_split['TLD']}"
        logger.verbose(f"Determined domain: {domain}")
        
        cache = None if not (self.cache and self.cache.is_exist(fqdn)) else self.cache.get(fqdn)

        zone_id = self.get_zone_id(domain) if not cache else cache["zone_id"]
        dns_record_id = self.get_record_id(zone_id, fqdn) if not cache else cache["dns_record_id"]
        old_record: list[dict[str, Any]] = self.get_dns_records(zone_id, {"name": fqdn})
        if not old_record:
            raise KeyError(f"No domain name '{fqdn}' found in your DNS records. Please create it first.")

        self.__cmit(domain_type, zone_id, fqdn, dns_record_id)
        
        # Check if the content is already up-to-date
        if content == old_record[0]['content']:
            return logger.log(f"No changes needed for '{fqdn}', content is already up-to-date.")

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
        logger.verbose(f"Updating DNS record with data: {data}")
        response = requests.put(url, headers=self.headers, json=data)
        result = response.json()

        # Handle response errors
        if not response.ok:
            raise ConnectionError(f"Error updating DNS record. Response Code: {response.status_code}, Error: {response.text}")

        if not result.get("success", False):
            raise ConnectionRefusedError(f"Failed to update content of '{fqdn}' to '{content}'. Errors: {result['errors']}")

        logger.log(f"Successfully updated DNS record for '{fqdn}' with new content: {content}")

logger = Logger(CloudFlare.integrate)
