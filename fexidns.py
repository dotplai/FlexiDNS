import configparser
from datetime import date, datetime, timedelta
import math
import sys
import asyncio
from typing import NoReturn, Self

from libs.converter import unixConvert

from libs.api.ipify import ipify
from libs.api.cloudflare import CloudFlare
from libs.api.noip import NoIP
from libs.api.dyndns import DynDNS
from libs.logger import logger, LoggedException

import json
from ipaddress import ip_address
import argparse

class Logger:
    def __init__(self, integrate: str):
        self.integrate = integrate

    def set_integrate(self, integrate: str) -> Self:
        self.integrate = integrate
        return self
    
    def log(self, message: any, level: int | str = 20) -> None:
        logger.log(level=level, msg=message, extra={"api": self.integrate})   
    
    def verbose(self, message: any, level: int | str = 10) -> None:
        logger.log(level=level, msg=message, extra={"api": self.integrate})
__logger__ = Logger("FlexiDNS")

# Load configuration
config = configparser.ConfigParser(allow_no_value=True, default_section='General')
config.read('config.ini')

# Identify enabled APIs
enabled_apis = [_ for _ in config.sections() if _ and config.getboolean(_, "enabled", fallback=False)]

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
    FQDNObjects = json.loads(config.get(section, "FQDN").strip("',"))
    print(FQDNObjects)
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
        except Exception as e:
            LoggedException(integrate).exception(e)

class AsynchronousPeriodic:
    """Asynchronous loop for periodic tasks."""
    integrate = 'AsynchronousPeriodic'
    def __init__(self: Self) -> None:
        self.syncLogger = __logger__.set_integrate(self.integrate)

    async def sync(self,) -> None:
        """Run the asynchronous loop.""" 
        try:
            Iaddress: list[str] = str(ipify(64).get_address(format='text')).split('or')
            IAObjects: dict = {
                "Iv4": Iaddress[0] if ip_address(Iaddress[0]).version == 4 else None,
                "Iv6": Iaddress[1] if len(Iaddress) > 1 and ip_address(Iaddress[1]).version == 6 else None
            }
            
            if not (IAObjects["Iv4"] or IAObjects["Iv6"]):
                return self.syncLogger.log(f"Public IPv4 and IPv6 not retrieved, skipping update", 30)
            
            # Update all enabled APIs
            tasks = []
            if 'A' in CloudFlareFQDN and IAObjects['Iv4']:
                tasks.append(integrateInstance("CloudFlare", CloudFlareAPI, CloudFlareFQDN['A'], IAObjects['Iv4']))
            if 'AAAA' in CloudFlareFQDN and IAObjects["Iv6"]:
                tasks.append(integrateInstance("CloudFlare", CloudFlareAPI, CloudFlareFQDN['AAAA'], IAObjects["Iv6"]))
            
            if tasks:
                await asyncio.gather(*tasks)
        except Exception as e:
            LoggedException(self.integrate).exception(e)

    async def intervaltime(self: Self, syncTime: int) -> NoReturn:
        """Periodic loop to update DNS records at specified intervals."""
        self.syncLogger.log(f"Starting periodic DNS updates every {syncTime//60} minutes ({syncTime}s).")
        
        while True:
            start_time = asyncio.get_event_loop().time()
            await self.sync()
            elapsed_time = asyncio.get_event_loop().time() - start_time
            sleep_time = max(0, syncTime - elapsed_time)
            self.syncLogger.log(f"Cycle completed in {elapsed_time:.2f}s. Sleeping for {sleep_time:.2f}s.")
            await asyncio.sleep(sleep_time)
    
    async def unix(self: Self, uinx_time: float | int) -> NoReturn:
        self.syncLogger.log(f"Starting periodic DNS updates on unix time {uinx_time}.")
        if uinx_time > 86_400: raise ValueError("Unix time must be less than 86,400 seconds (24 hours).")

        while True:
            now = datetime.now()
            uinxTime = unixConvert(uinx_time)
            target_time = now.replace(hour=uinxTime[2], minute=uinxTime[1], second=uinxTime[0], microsecond=0)
            
            if now >= target_time: target_time += timedelta(days=1)
            time_to_wait = (target_time - now).total_seconds()
            self.syncLogger.log(f"Waiting {time_to_wait} seconds until {target_time.ctime()}...")
            await asyncio.sleep(time_to_wait)
            await self.sync()
            self.syncLogger.log(f"Cycle completed. Sleeping until next scheduled time.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="FlexiDNS Dynamic Updater")
    parser.add_argument("-m", "--mode", type=str, choices=["unix", "interval", "prefer"], help="Looping method: 'unix' or 'interval'")
    parser.add_argument("-t", "--synctime", type=int, help="The sync time specifies the time between each loop check and update.")
    args = parser.parse_args()
    
    # Conditional validation
    if args.mode in ["unix", "interval"] and args.synctime is None:
        parser.error(f"--synctime (-t) is required when --mode is '{args.mode}'")

    mode = args.mode or config.get("General", "mode").strip('",')
    syncTime = math.nan if args.mode in ['prefer'] else args.synctime if args.synctime else config.getint("General", "syncTime", fallback=600)
    try:
        if mode in ["intervalTime", "interval"]:
            syncTime*=60
            __logger__.log(f"Starting periodic DNS updates every {syncTime//60} minutes.")
            asyncio.run(AsynchronousPeriodic().intervaltime(syncTime))
        elif mode in ["unixEpoch", "unix"]:
            if syncTime > 86_400 and not syncTime: raise ValueError("Unix time must be less than 86,400 seconds (24 hours).")
            asyncio.run(AsynchronousPeriodic().unix(syncTime))
        elif args.mode in ['prefer']:
            asyncio.run(AsynchronousPeriodic().sync())
            __logger__.log("Preferred one-time sync completed.")
            sys.exit(0)

        else: raise ValueError("mode must be either 'intervalTime' or 'unixEpoch'.")
    except KeyboardInterrupt as e:
        __logger__.log("KeyboardInterrupt detected. Exiting...", level=10)
        sys.exit(0)
