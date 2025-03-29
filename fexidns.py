import configparser
import sys
import asyncio
from typing import NoReturn
from libs.api.ipify import ipify
from libs.api.cloudflare import CloudFlare
from libs.api.noip import NoIP
from libs.api.dyndns import DynDNS
from libs.logger import logger, LoggedException

class Logger:
    def __init__(self, integrate: str):
        self.integrate = integrate
    
    def log(self, message: any, level: int | str = 20, temp_integrate: str = None):
        logger.log(level=level, msg=message, extra={"api": temp_integrate or self.integrate})   
    
    def verbose(self, message: any, level: int | str = 10, temp_integrate: str = None):
        logger.log(level=level, msg=message, extra={"api": temp_integrate or self.integrate})
__logger__ = Logger("FlexiDNS")

# Load configuration
config = configparser.ConfigParser(allow_no_value=True, default_section='General')
config.read('config.ini')

# Identify enabled APIs
enabled_apis = [_ for _ in config.sections() if _ and config.getboolean(_, "enabled", fallback=False)]
looping_method = config.get("General", "loopingMethod", fallback="interval_time")
if looping_method not in ["interval_time"]:
    raise ValueError("loopingMethod must be either 'interval_time'.")
interval_time = config.getint("General", "intervalTime", fallback=800) * 60

global domain_type

def initialize_api(section, cls) -> tuple[None, list] | tuple[any, dict[str, any | list]]:
    """Initialize API clients dynamically based on config."""
    if not section: return None, []
    
    credentials = {
        "email": config.get(section, "email", fallback="").strip('",'),
        "password": config.get(section, "password", fallback="").strip('",')
    }
    cache = {
        "cache_timeout": config.getint(section, "cacheTimeout", fallback="172800"),
        "cache_persistent": config.getboolean(section, "cachePersistent", fallback="False")
    }
    
    fqdns_ATC = config.get(section, "FQDNv4", fallback="[]").strip('",')
    fqdn_A4TC = config.get(section, "FQDNv6", fallback="[]").strip('",')
    fqdns_ATL = eval(fqdns_ATC) if fqdns_ATC.startswith("[") and fqdns_ATC.endswith("]") else []
    fqdns_A4TL = eval(fqdn_A4TC) if fqdn_A4TC.startswith("[") and fqdn_A4TC.endswith("]") else []
    
    return cls(**credentials,**cache), {'A': fqdns_ATL, 'AAAA': fqdns_A4TL}

# Initialize APIs
cloudflare_api, cloudflare_fqdns  = initialize_api("CloudFlare", CloudFlare)

async def integrateInstance(integrate: str, instance: any, fqdns: list, content: str, domain_type: str) -> None:
    """Update DNS records for a given API."""
    if not instance: return
    
    for fqdn in fqdns:
        try:
            __logger__.log(f"Updating record: {fqdn} -> {content}", temp_integrate=integrate)
            if domain_type == "A":
                instance.A(fqdn, content)
            elif domain_type == "AAAA":
                instance.AAAA(fqdn, content)
            else:
                raise ValueError(f"Unsupported domain type: {domain_type}")

            __logger__.log(f"Record updated successfully: {fqdn} -> {content}", temp_integrate=integrate)
        except Exception as e:
            LoggedException(e, api=integrate)

async def interval_loop() -> NoReturn:
    """Efficient periodic DNS update loop."""
    __logger__.verbose(f"Starting periodic DNS updates every {interval_time//60} minutes.")
    
    cloudflare_fqdns_ATL = cloudflare_fqdns.get('A', [])
    cloudflare_fqdns_A4TL = cloudflare_fqdns.get('AAAA', [])
    
    while True:
        start_time = asyncio.get_event_loop().time()
        
        try:
            ipv4_address: str = ipify(4).get_address(format='json').json().get('ip', '')
            ipv6_address: str = ipify(6).get_address(format='json').json().get('ip', '')
            
            if not (ipv4_address or ipv6_address):
                __logger__.log(f"Public IPv4 and IPv6 not retrieved, skipping update", 30)
                continue
            
            # Update all enabled APIs
            if looping_method == "interval_time":
                await asyncio.gather(
                    integrateInstance("CloudFlare", cloudflare_api, cloudflare_fqdns_ATL, ipv4_address, domain_type="A"),
                    integrateInstance("CloudFlare", cloudflare_api, cloudflare_fqdns_A4TL, ipv6_address, domain_type="AAAA"),
                )
        except Exception as e:
            LoggedException(e)
        
        elapsed_time = asyncio.get_event_loop().time() - start_time
        sleep_time = max(0, interval_time - elapsed_time)
        __logger__.verbose(f"Cycle completed in {elapsed_time:.2f}s. Sleeping for {sleep_time:.2f}s.")
        await asyncio.sleep(sleep_time)

if __name__ == '__main__':
    print(f"Interval time set to {interval_time//60} minutes.")
    
    try:
        user_input = input("Enter new interval time (minutes) or press Enter to keep default: ")
        interval_time = int(user_input) * 60 if user_input else interval_time
    except ValueError:
        LoggedException(TypeError("Invalid input for interval_time."))
    
    __logger__.log(f"Starting DNS update loop with interval {interval_time//60} minutes.")
    
    try:
        asyncio.run(interval_loop())
    except KeyboardInterrupt:
        __logger__.verbose("KeyboardInterrupt detected. Exiting...")
        sys.exit(0)
