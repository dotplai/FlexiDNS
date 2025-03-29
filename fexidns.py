import configparser
from datetime import date, datetime, timedelta
from libs.converter import unixConvert
from time import time
import sys
import asyncio
from typing import NoReturn, Self

from libs.api.ipify import ipify
from libs.api.cloudflare import CloudFlare
from libs.api.noip import NoIP
from libs.api.dyndns import DynDNS
from libs.logger import logger, LoggedException

from json import loads
from ipaddress import ip_address

class Logger:
    def __init__(self, integrate: str):
        self.integrate = integrate

    def set_integrate(self, integrate: str) -> Self:
        self.integrate = integrate
    
    def log(self, message: any, level: int | str = 20):
        logger.log(level=level, msg=message, extra={"api": self.integrate})   
    
    def verbose(self, message: any, level: int | str = 10):
        logger.log(level=level, msg=message, extra={"api": self.integrate})
__logger__ = Logger("FlexiDNS")

# Load configuration
config = configparser.ConfigParser(allow_no_value=True, default_section='General')
config.read('config.ini')

# Identify enabled APIs
enabled_apis = [_ for _ in config.sections() if _ and config.getboolean(_, "enabled", fallback=False)]
looping_method = config.get("General", "loopingMethod", fallback="interval_time")
interval_time = config.getint("General", "intervalTime", fallback=800) * 60

def initialize_api(section: str, cls: any) -> tuple[any, dict[str, list]]:
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
    
    FQDNObjects = loads(config.get(section, "FQDN"))
    
    return cls(**credentials,**cache), FQDNObjects

# Initialize APIs
CloudFlareAPI, CloudFlareFQDN = initialize_api("CloudFlare", CloudFlare)

async def integrateInstance(integrate: str, instance: any, fqdns: list, content: str) -> None:
    """Update DNS records for a given API."""
    Tintegrate = __logger__.set_integrate(integrate)
    if not instance: return
    
    for fqdn in fqdns:
        try:
            Tintegrate.log(f"Updating record: {fqdn} -> {content}")
            if ip_address(content).version.__eq__(4):
                instance.A(fqdn, content)
            elif ip_address(content).version.__eq__(6):
                instance.AAAA(fqdn, content)

            Tintegrate.log(f"Record updated successfully: {fqdn} -> {content}")
        except Exception as e:
            LoggedException(e, api=integrate)

class AsynchronousPeriodic:
    """Asynchronous loop for periodic tasks."""
    integrate = 'AsynchronousPeriodic'
    Tintegrate = __logger__.set_integrate(integrate)

    @classmethod
    async def intervaltime(cls, interval_time: int) -> NoReturn:
        """Periodic loop to update DNS records at specified intervals."""
        cls.Tintegrate.log(f"Starting periodic DNS updates every {interval_time//60} minutes ({interval_time}s).")
        
        while True:
            start_time = asyncio.get_event_loop().time()
            await cls.update()
            elapsed_time = asyncio.get_event_loop().time() - start_time
            sleep_time = max(0, interval_time - elapsed_time)
            __logger__.log(f"Cycle completed in {elapsed_time:.2f}s. Sleeping for {sleep_time:.2f}s.")
            await asyncio.sleep(sleep_time)
    
    @classmethod
    async def unix(cls, uinx_time: float | int) -> NoReturn:
        cls.Tintegrate.log(f"Starting periodic DNS updates on unix time {uinx_time}.")

        if uinx_time > 86_400: raise ValueError("Unix time must be less than 86,400 seconds (24 hours).")

        while True:
            now = datetime.now()
            uinxTime = unixConvert(uinx_time)
            target_time = now.replace(hour=uinxTime[3], minute=uinxTime[2], second=uinxTime[1], microsecond=uinxTime[0])
            
            if now >= target_time: target_time += timedelta(days=1)
            time_to_wait = (target_time - now).total_seconds()
            cls.Tintegrate.log(f"Waiting {time_to_wait} seconds until {target_time.ctime()}...")
            await asyncio.sleep(time_to_wait)
            await cls.update()
            cls.Tintegrate.log(f"Cycle completed. Sleeping until next scheduled time.")

    @classmethod
    async def update(cls) -> None:
        """Run the asynchronous loop."""
        try:
            Iaddress: str = ipify(64).get_address(format='json').split('or')
            IAObjects: dict = {
                "Iv4": Iaddress[0] if ip_address(Iaddress[0]).version == 4 else None,
                "Iv6": Iaddress[1] if len(Iaddress) > 1 and ip_address(Iaddress[1]).version == 6 else None
            }
            
            if not Iaddress:
                cls.Tintegrate.log(f"Public IPv4 and IPv6 not retrieved, skipping update", 30)
                return
            
            # Update all enabled APIs
            await asyncio.gather(
                integrateInstance("CloudFlare", CloudFlareAPI, CloudFlareFQDN['A'], IAObjects['Iv4']), 
                integrateInstance("CloudFlare", CloudFlareAPI, CloudFlareFQDN['AAAA'], IAObjects["Iv6"])
            )
        except Exception as e:
            LoggedException(e)

if __name__ == '__main__':
    try:
        if looping_method not in ["interval_time", "unix"]:
            raise ValueError("loopingMethod must be either 'interval_time' or 'unix'.")
        if looping_method == "interval_time":
            interval_time = config.getint("General", "intervalTime", fallback=800) * 60
            if interval_time > 86_400: raise ValueError("Interval time must be less than 86,400 seconds (24 hours).")
            __logger__.log(f"Starting periodic DNS updates every {interval_time//60} minutes.")
            asyncio.run(AsynchronousPeriodic.intervaltime(interval_time))

        elif looping_method == "unix":
            unix_time = float(input("Enter the unix time (in seconds) for periodic updates: ")) if looping_method == "unix" else None
            if unix_time > 86_400 and not unix_time: raise ValueError("Unix time must be less than 86,400 seconds (24 hours).")
            asyncio.run(AsynchronousPeriodic.unix(unix_time))
        else:
            raise ValueError("Invalid looping method specified.")
    except KeyboardInterrupt as e:
        __logger__.log("KeyboardInterrupt detected. Exiting...", level=10)
        sys.exit(0)
