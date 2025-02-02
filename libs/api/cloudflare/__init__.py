import json
import math
from typing import Literal, Optional, Self, TypeAlias
from deprecated import deprecated
import requests
from libs.logger import LoggedException, logger
from libs.api.cloudflare.__cache__ import RecordsCache

class Logger:
    def __init__(self, integrate: str):
        self.integrate = integrate
    def __logging__(self, message: any, level: int | str = 20, temporary_integrate: str = None):
        logger.log(level=level, msg=message, extra={"api": temporary_integrate if temporary_integrate else self.integrate})   
    def __verbose__(self, message: any, level: int | str = 10,  temporary_integrate: str = None):
        logger.log(level=level, msg=message, extra={"api": temporary_integrate if temporary_integrate else self.integrate})

class CloudFlare:
    integrate = 'CloudFlare'
    
    def __init__(self: Self, email: str, password: str, cache_timeout: int = 86400, cache_persistent: bool = False):
        __logger__.__verbose__("Initializing CloudFlare API authorization...")
        
        self.headers = {
            "Content-Type": "application/json",
            "X-Auth-Email": email,
            "Authorization": f"Bearer {password}"
        }
        
        _ct = math.inf if cache_timeout.__le__(-1) else cache_timeout
        self.cache: Optional[type[RecordsCache]] = RecordsCache().build(timeout=_ct) if _ct.__ne__(0) else None
        self.cache_persistent = cache_persistent
        
    def getZoneId(self: Self, domain: str) -> str:
        url = "https://api.cloudflare.com/client/v4/zones"
        __logger__.__verbose__(f"Fetching zone id for domain: {domain}")

        response = requests.get(url, headers=self.headers, params={"name": domain})
        data = response.json()

        if not response.ok:
            LoggedException(ConnectionError(f"Error fetching zone id for domain '{domain}'. Response Code: {response.status_code}, Error: {response.text}"), integrate)

        if data['success'] and data['result']:
            zone_id = data['result'][0]['id']
            __logger__.__verbose__(f"Zone ID retrieved for domain '{domain}': {zone_id}")
            return zone_id
        else:
            LoggedException(ConnectionRefusedError("Domain not found or API call unsuccessful."), integrate)

    def getRecordId(self: Self, zone_id: str, record_name: str) -> str:
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        __logger__.__verbose__(f"Fetching DNS record ID for record: {record_name} in zoneId: {zone_id}")

        response = requests.get(url, headers=self.headers, params={"name": record_name})
        data = response.json()

        if not response.ok:
            LoggedException(ConnectionError(f"Error fetching DNS record. Response Code: {response.status_code}, Error: {response.text}"), integrate)

        if data['success'] and data['result']:
            record_id = data['result'][0]['id']
            __logger__.__verbose__(f"DNS record ID retrieved for record '{record_name}': {record_id}")
            return record_id
        else:
            LoggedException(ConnectionRefusedError("DNS record not found or API call unsuccessful."), integrate)

    def getDNSRecord(self: Self, zone_id: str, filter: object = None) -> dict:
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        __logger__.__verbose__(f"Fetching DNS records for zoneId: {zone_id} with filter: {filter}")

        response = requests.get(url, headers=self.headers, params=filter)
        response.raise_for_status()
        data = response.json()

        if not response.ok:
            LoggedException(ConnectionError(f"Error fetching DNS records. Response Code: {response.status_code}, Error: {response.text}"), integrate)

        __logger__.__verbose__(f"DNS records retrieved: {data['result']}")
        return data['result']

    def A(self: Self, fqdn: str, content: str, ttl: int = None, proxied: bool = None, comment: str = None) -> None:
        """
        Update an A record in Cloudflare's DNS using the provided parameters.
        Handles caching for ZoneID and DNSRecordID to improve performance.
        """
        if self.cache:
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

        # Split FQDN into components
        __logger__.__verbose__(f"Processing A record update for FQDN: {fqdn}, Content: {content}")
        parts = fqdn.split('.')
        fqdn_split = {
            "TLD": parts[-1],
            "DN": parts[-2] if len(parts) > 1 else None,
            "SDN": ".".join(parts[:-2]) if len(parts) > 2 else None
        }
        __logger__.__verbose__(f"FQDN split into TLD: {fqdn_split['TLD']}, DN: {fqdn_split['DN']}, SDN: {fqdn_split['SDN']}")

        domain = f"{fqdn_split['DN']}.{fqdn_split['TLD']}"
        __logger__.__verbose__(f"Determined domain: {domain}")
        
        cache = None if not (self.cache and self.cache.is_exist(fqdn)) else self.cache.get(fqdn)

        zone_id = self.getZoneId(domain) if not cache else cache["zone_id"]
        dns_record_id = self.getRecordId(zone_id, fqdn) if not cache else cache["dns_record_id"]
        old_record: dict = self.getDNSRecord(zone_id, {"name": fqdn})
        if not old_record:
            LoggedException(KeyError(f"No domain name '{fqdn}' found in your DNS records. Please create it first."), integrate)

        # Cache the retrieved ZoneID and DNSRecordID if caching is enabled
        if self.cache:
            data = {
                "zone_id": zone_id, "dns_record_id": dns_record_id
            }
            
            if not self.cache.is_exist(fqdn):
                self.cache.append(fqdn, data)
                __logger__.__verbose__(f"Appended cache with {data}.")
            elif self.cache.is_exist(fqdn) and not self.cache.is_valid(fqdn):
                self.cache.inject(fqdn, data)
                __logger__.__verbose__(f"Updated cache with {data}.")
            
            if self.cache_persistent:
                data = self.cache.read()
                
                if not self.cache.is_same(data):
                    self.cache.commit()
                    __logger__.__verbose__("Committed cache to Persistent Cache.")
                else: __logger__.__verbose__("No changes needed for Persistent Cache is is already up-to-date.")
        
        # Check if the content is already up-to-date
        if content == old_record[0]['content']:
            return __logger__.__logging__(f"No changes needed for '{fqdn}', content is already up-to-date.")

        # Prepare data for the DNS record update
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}"
        data = {
            "type": "A",
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
            LoggedException(ConnectionError(f"Error updating DNS record. Response Code: {response.status_code}, Error: {response.text}"), integrate)

        if not result.get("success", False):
            LoggedException(ConnectionRefusedError(f"Failed to update content of '{fqdn}' to '{content}'. Errors: {result['errors']}"), integrate)

        __logger__.__logging__(f"Successfully updated DNS record for '{fqdn}' with new content: {content}")

    def AAAA(self: Self, fqdn: str, content: str, ttl: int = None, proxied: bool = None, comment: str = None) -> None:
        """
        Update an AAAA record in Cloudflare's DNS using the provided parameters.
        Handles caching for ZoneID and DNSRecordID to improve performance.
        """
        print("AAAA records still under-developments...")
        print(" - About AAAA records are used to resolve a domain name which corresponds to an IPv6 address.")
        return

__logger__ = Logger(CloudFlare.integrate)