import configparser
from datetime import date, datetime, timedelta
import math
import sys
import asyncio
from typing import NoReturn, Self, Union

from libs.logging import Logger
from libs.converter import unixConvert

from libs.api.ipify import ipify
from libs.api.cloudflare import CloudFlare
from libs.api.noip import NoIP
from libs.api.dyndns import DynDNS

import json
from ipaddress import ip_address
import argparse

logger = Logger("FlexiDNS")

# Load configuration
config = configparser.ConfigParser(allow_no_value=True, default_section='General')
config.read('config.ini')

def initialize_api() -> tuple[dict, list]:
    section = [_ for _ in config.sections() if _ and config.getboolean(_, "enabled", fallback=False)]
    if not section: return ({}, [])

    for _ in section:
        credentials = {
            "email": config.get(_, "email", fallback="").strip('",'),
            "password": config.get(_, "password", fallback="").strip('",')
        }
        cache = {
            "cache_timeout": config.getint(_, "cacheTimeout", fallback="172800"),
            "cache_persistent": config.getboolean(_, "cachePersistent", fallback="False")
        }

        object_fqdn = {
            _: json.loads(config.get(_, "FQDN").strip("',"))
        }

        apis = {
            _: globals()[_](**credentials, **cache)
        }

    return apis, object_fqdn

# Initialize APIs
APIs, ObjectFQDNs = initialize_api()

async def call(instance: any, fqdns: list, content: str) -> None:
    """Update DNS records for a given API."""
    sync_logger = logger.set_integrate(instance.__class__.__name__)
    if not instance: return
    
    for fqdn in fqdns:
        try:
            sync_logger.log(f"Updating record: {fqdn} -> {content}")
            if ip_address(content).version.__eq__(4):
                instance.A(fqdn, content)
            elif ip_address(content).version.__eq__(6):
                instance.AAAA(fqdn, content)
        except Exception as e:
            sync_logger.exception(e)

class AsynchronousPeriodic:
    """Asynchronous loop for periodic tasks."""
    integrate = 'AsynchronousPeriodic'
    def __init__(self: Self) -> None:
        self.sync_logger = logger.set_integrate(self.integrate)

    async def sync(self: Self) -> None:
        """Run the asynchronous loop.""" 
        try:
            inet_address: list[str] = str(ipify(64).get_address(format='text')).split('or')
            inet_address_object: dict = {
                "Iv4": inet_address[0] if ip_address(inet_address[0]).version == 4 else None,
                "Iv6": inet_address[1] if len(inet_address) > 1 and ip_address(inet_address[1]).version == 6 else None
            }
            
            if not (inet_address_object["Iv4"] or inet_address_object["Iv6"]):
                return self.sync_logger.log("Public IPv4 and IPv6 not retrieved, skipping update", 30)
            
            # Update all enabled APIs
            tasks = []
            for object_name in APIs:
                record_types = {
                    'A': ('A', 'Iv4'),
                    'AAAA': ('AAAA', 'Iv6')
                }
                
                for dns_type, (record, ip_ver) in record_types.items():
                    if dns_type in ObjectFQDNs[object_name] and inet_address_object[ip_ver]:
                        tasks.append(call(
                            APIs[object_name],
                            ObjectFQDNs[object_name][record],
                            inet_address_object[ip_ver]
                        ))

            if tasks:
                await asyncio.gather(*tasks)
        except Exception as e:
            self.sync_logger.exception(e)

    async def interval(self: Self, sync_time: int) -> NoReturn:
        self.sync_logger.log(f"Starting periodic DNS updates every {sync_time//60} minutes ({sync_time}s).")
        
        while True:
            start_time = asyncio.get_event_loop().time()
            await self.sync()
            elapsed_time = asyncio.get_event_loop().time() - start_time
            sleep_time = max(0, sync_time - elapsed_time)
            self.sync_logger.log(f"Cycle completed in {elapsed_time:.2f}s. Sleeping for {sleep_time:.2f}s.")
            await asyncio.sleep(sleep_time)
    
    async def unix(self: Self, uinx_time: float | int) -> NoReturn:
        unixl = unixConvert(uinx_time)
        self.sync_logger.log(f"Starting periodic DNS updates at {unixl[2]:02d}:{unixl[1]:02d}:{unixl[0]:02d} (24hr) each day.")
        if uinx_time > 86_400: raise ValueError("Unix time must be less than 86,400 seconds (24 hours).")

        while True:
            now = datetime.now()
            target_time = now.replace(hour=unixl[2], minute=unixl[1], second=unixl[0], microsecond=0)
            
            if now >= target_time: target_time += timedelta(days=1)
            time_to_wait = (target_time - now).total_seconds()
            self.sync_logger.log(f"Waiting {time_to_wait} seconds until {target_time.ctime()}...")
            await asyncio.sleep(time_to_wait)
            await self.sync()
            self.sync_logger.log("Cycle completed. Sleeping until next scheduled time.")

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
        logger.log(f"<=== Mode Set as {mode} ===>")
        if mode in ["intervalTime", "interval"]:
            syncTime*=60
            asyncio.run(AsynchronousPeriodic().interval(syncTime))
        elif mode in ["unixEpoch", "unix"]:
            if syncTime > 86_400 and not syncTime: raise ValueError("Unix time must be less than 86,400 seconds (24 hours).")
            rtime = unixConvert(syncTime)
            asyncio.run(AsynchronousPeriodic().unix(syncTime))
        elif args.mode in ['prefer']:
            asyncio.run(AsynchronousPeriodic().sync())
            logger.log("Preferred one-time sync completed.")
            sys.exit(0)

        else: raise ValueError("mode must be either 'intervalTime' or 'unixEpoch'.")
    except KeyboardInterrupt as e:
        logger.log("KeyboardInterrupt detected. Exiting...", level=10)
        sys.exit(0)
