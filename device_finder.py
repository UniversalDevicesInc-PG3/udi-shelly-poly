import asyncio
from typing import Any, Optional, cast

from zeroconf import IPVersion, ServiceBrowser, ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncServiceInfo, AsyncZeroconf

async def async_get_services(aiozc: AsyncZeroconf,service_type, device_name, loops, wait) -> None:
    devices = {}  
    zeroconf = aiozc.zeroconf
    for x in range(loops):  # How many seconds to allow the query
        infos = []
        for name in zeroconf.cache.names():
            if not name.endswith(service_type):
                continue
            if not name.startswith(device_name):
                continue
            infos.append(AsyncServiceInfo(service_type, name))
        tasks = [info.async_request(aiozc.zeroconf, 1000) for info in infos]
        await asyncio.gather(*tasks)
        for info in infos:
                addresses = ["%s:%d" % (addr, cast(int, info.port)) for addr in info.parsed_addresses()]
                assert addresses[0]
                devices[info.name] = addresses[0]
        await asyncio.sleep(wait)
    return devices


#Looks for a MDNS device on using the [service_type] with a name that begins with [device_name]
# It looks [loops] times waiting [wait] seconds between each loop.  So total delay time is (loops * wait)
class Device_Finder:
    def __init__(self,  device_name: str, service_type = "_http._tcp.local.",loops = 10, wait = 0.5) -> None:
        self.threaded_browser: Optional[ServiceBrowser] = None
        self.aiozc: Optional[AsyncZeroconf] = None
        self.ip_version = IPVersion.V4Only
        self.devices = {}
        self.service_type = service_type
        self.device_name = device_name
        self.loops = loops
        self.wait = wait

    #looks for the devices as specified in the constructor.  Returns a dictionary giving the 
    #matching device DNS names and the IP address.
    def look_for_devices(self) -> Any:
        loop = self.get_or_create_eventloop()#asyncio.get_event_loop()
        loop.run_until_complete(self.async_run())
        loop.run_until_complete(self.async_close())
        return self.devices

    async def async_run(self) -> None:
        self.aiozc = AsyncZeroconf(ip_version=self.ip_version)
        assert self.aiozc is not None

        def on_service_state_change(
            zeroconf: Zeroconf, service_type: str, state_change: ServiceStateChange, name: str
        ) -> None:
            """Dummy handler."""

        self.threaded_browser = ServiceBrowser(
            self.aiozc.zeroconf, [self.service_type], handlers=[on_service_state_change]
        )
        self.devices = await async_get_services(self.aiozc,self.service_type, self.device_name, self.loops , self.wait )

    async def async_close(self) -> None:
        assert self.aiozc is not None
        assert self.threaded_browser is not None
        self.threaded_browser.cancel()
        await self.aiozc.async_close()

    def get_or_create_eventloop(self):
        try:
            return asyncio.get_event_loop()
        except RuntimeError as ex:
            if "There is no current event loop in thread" in str(ex):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return asyncio.get_event_loop()