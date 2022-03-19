import enum
import asyncio
import json
from typing import Any

from aiohttp import ClientSession, ClientResponseError,ClientTimeout, BasicAuth, ClientConnectorError
from ShellyDevice_Constants import *

EP_TIMEOUT = ClientTimeout(
    total=3  # It on LAN, and if too long we will get warning about the update duration in logs
)

class DeviceConnectorError(Exception):
   pass


class ShellyDevice_Base:
    """Controller class for the Shelly1 """

    def __init__(self, host: str, user: str = None, pwd: str = None, session: ClientSession = None):
        """Initialize a Shelly1."""
        self._host = host
        self._base_url = "http://" + host + "/"
        self.primary_output_channel = None
        self.primary_status_channel = None
        self.auth_cred = None
        if( user is not None and pwd is not None):
            self.auth_cred = BasicAuth(user,pwd)


    @property
    def host(self) -> str:
        """Get the IP used by this client."""
        return self._host
    #
    # Device Information Funtions
    #
    def get_device_settings(self) -> Any:
        """Retrieve the device configuration information."""
        json_settings = asyncio.run(self._send_request("settings"))
        if json_settings is None:
            return None
        settings_dict = json.loads(json_settings)
        return settings_dict

    def get_device_info(self) -> Any:
        """Provides basic information about the device. This does not require HTTP authentication. Can be used in for device discovery and identification."""
        return asyncio.run( self._send_request( "shelly"))

    def get_device_status(self) -> Any:
        """Retrieve the device status information such as free ram, free memory, and uptime."""
        json_status =   asyncio.run( self._send_request("status"))
        if json_status is None:
            return None
        status_dict = json.loads(json_status)
        return status_dict

    def get_device_is_on(self) -> bool:
            """is the device turned on or not"""
            assert(self.primary_status_channel != None )  # Need to set primary status channel in derived class __init__
            
            json_state =  self.get_device_status()
            if json_state is None:
                return False
            return json_state[self.primary_status_channel][0]['ison']

    #
    # Device Action Functions
    #  
    def device_reboot(self) -> Any:
        """Retrieve the device information."""
        return asyncio.run( self._send_request( "reboot"))

    def device_turn_on(self,timer: int = None) -> Any:
        """Turns on  device.  Optional parameter specifies automatic flip-back timer in seconds (e.g. turned On or OFF for X seconds and will be switched back to previous state after that)"""
        assert(self.primary_output_channel != None )  # Need to set primary channel in derived class __init__
        cmd = self.primary_output_channel + '?turn=on'
        if timer != None:
            cmd += "&timer="+str(timer)
        return asyncio.run( self._send_request(cmd ))

    def device_turn_off(self) -> Any:
        """Turns off relay device"""
        assert(self.primary_output_channel != None )  # Need to set primary channel in derived class __init__
        cmd = self.primary_output_channel + '?turn=off'
        return asyncio.run( self._send_request(cmd ))


    def device_set_on_state(self,state: POWER_STATE,timer: int = None) -> Any:
        """Accepted values: on, off or toggle.  Optional parameter specifies automatic flip-back timer in seconds (e.g. turned On or OFF for X seconds and will be switched back to previous state after that)"""
        assert(self.primary_output_channel != None )  # Need to set primary channel in derived class __init__
        cmd = self.primary_output_channel + '?turn='+str(state.value)
        if timer != None:
            cmd += "&timer="+str(timer)
        return asyncio.run( self._send_request(cmd ))

    #
    # Private functions
    #
    async def _send_request( self, endpoint: str, data: Any = None, retry: int = 1 ) -> Any:
        """Send a request"""
        session = ClientSession(raise_for_status=True, timeout=EP_TIMEOUT, auth=self.auth_cred )
        try:
            response = await session.request(
                 method="GET" if data is None else "POST",
                 url=self._base_url + endpoint,
                 json=data,
                 timeout=EP_TIMEOUT,
             )
            data = await response.text()
            await session.close()
            return data

        except ClientConnectorError:
            await session.close()
            raise  DeviceConnectorError

        except asyncio.TimeoutError:
            await session.close()

        except ClientResponseError as err:
            if err.code == 401 and retry > 0:
                return await self._send_request(endpoint, data, retry - 1)
            await session.close()
            raise
        except:
            await session.close()
            raise
       
