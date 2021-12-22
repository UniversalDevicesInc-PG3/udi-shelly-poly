import logging
import enum
import asyncio
import json
from types import BuiltinFunctionType
from typing import Any

from aiohttp import ClientSession, ClientResponseError,ClientTimeout

EP_TIMEOUT = ClientTimeout(
    total=3  # It on LAN, and if too long we will get warning about the update duration in logs
)
     
class POWER_ON_STATE(enum.Enum):
    """Power On States supported by Shelly_RGBW2_Client API."""
    Off            = "off"
    On             = "on"
    Last           = "last"

class BUTTON_INPUT_TYPE(enum.Enum):
    """List of Button Input Types supported by Shelly_RGBW2_Client API."""
    Momentary = "momentary"
    Toggle    = "toggle"
    Edge      = "edge"
    Detached  = "detached"
    Action    = "action"

class POWER_STATE(enum.Enum):
    """Power On States supported by Shelly_RGBW2_Client API."""
    Off            = "off"
    On             = "on"
    Toggle         = "toggle"

class LED_COLOR:
    def __init__(self,  red: int =None, green: int =None, blue: int =None, white: int =None, brightness: int =None, on: bool = None,timer: int = None):
        """Initialize  the LED color class"""
        self.red         = red
        self.green       = green
        self.blue        = blue
        self.white       = white
        self.brightness  = brightness
        self.on          = on
        self.timer       = timer

    def __str__(self):
        return "LED Colors: red=" + str(self.red) + ",  green=" + str(self.green) + ",  blue=" + str(self.blue) + ",  white=" + str(self.white) + ",  brightness=" + str(self.brightness) + ",  on=" + str(self.on)  + ",  timer=" + str(self.timer)



class Shelly_RGBW2_Client:
    """Controller class for the Shelly_RGBW2 Color."""

    def __init__(self, host: str, session: ClientSession = None):
        """Initialize a Shelly_RGBW2_Client."""
        self._host = host
        self._base_url = "http://" + host + "/"


    @property
    def host(self) -> str:
        """Get the IP used by this client."""
        return self._host
    #
    # Device Information Funtions
    #
    def get_device_settings(self) -> Any:
        """Retrieve the device configuration information."""
        return asyncio.run(self.__send_request("settings"))

    def get_device_info(self) -> Any:
        """Provides basic information about the device. This does not require HTTP authentication. Can be used in for device discovery and identification."""
        return asyncio.run( self.__send_request( "shelly"))

    def get_device_status(self) -> Any:
        """Retrieve the device status information such as free ram, free memory, and uptime."""
        return asyncio.run( self.__send_request("status"))

    def get_device_color_settings(self) -> Any:
            """Retrieve the device settings for color mode."""
            return asyncio.run( self.__send_request( "settings/color/0"))

    def get_device_color_state(self) -> Any:
            """Retrieve the device settings for color mode."""
            return asyncio.run( self.__send_request( "color/0"))

    def get_device_is_on(self) -> bool:
            """is the device turned on or not"""
            json_state =  self.get_device_color_state()
            state_dict = json.loads(json_state)
            return state_dict["ison"]

    def get_device_color(self) -> LED_COLOR:
            """is the device turned on or not"""
            json_state =  self.get_device_color_state()
            state_dict = json.loads(json_state)
            color = LED_COLOR(
                red        = state_dict["red"],
                green      = state_dict["green"],
                blue       = state_dict["blue"],
                white      = state_dict["white"],
                brightness = state_dict["gain"],
                on         = state_dict["ison"],
            )
            return color


    #
    # Device Action Functions
    #  
    def device_reboot(self) -> Any:
        """Retrieve the device information."""
        return asyncio.run( self.__send_request( "reboot"))

    def device_set_color_effect(self,effect: int) -> Any:
        """Set one of the effects from COLOR_EFFECT."""
        if not effect in range(0,4):
            return None
        cmd = "settings/color/0"+ "?effect="+str(effect)
        return asyncio.run( self.__send_request(cmd ))

    def device_set_default_color_transition(self,delay: int) -> Any:
        """Set transition time between on/off and color change, [0-5000] ms."""
        cmd = "settings/color/0"+ "?transition="+str(delay)
        return asyncio.run( self.__send_request(cmd ))

    def device_set_default_power_on_state(self,state: POWER_ON_STATE) -> Any:
        """Sets default power-on state: on, off or last"""
        cmd = "settings/color/0"+ "?default_state="+state.value
        return asyncio.run( self.__send_request(cmd ))

    def device_set_power_auto_on_time(self,time: int) -> Any:
        """Sets a default timer to turn ON after every OFF command in seconds."""
        cmd = "settings/color/0"+ "?auto_on="+str(time)
        return asyncio.run( self.__send_request(cmd ))

    def device_set_power_auto_off_time(self,time: int) -> Any:
        """Sets a default timer to turn OFF after every ON command in seconds."""
        cmd = "settings/color/0"+ "?auto_off="+str(time)
        return asyncio.run( self.__send_request(cmd ))

    def device_set_button_type(self,type: BUTTON_INPUT_TYPE) -> Any:
        """Input type: momentary, toggle, edge, detached or action."""
        cmd = "settings/color/0"+ "?btn_type="+type.value
        return asyncio.run( self.__send_request(cmd ))

    def device_set_button_invert_external_input(self,state: bool) -> Any:
        """Whether to invert external switch input."""
        cmd = "settings/color/0"+ "?btn_reverse="+str(int(state))
        return asyncio.run( self.__send_request(cmd ))

    def device_set_schedule_enabled(self,state: bool) -> Any:
        """Enable or disable schedule timer."""
        cmd = "settings/color/0"+ "?schedule="+str(int(state))
        return asyncio.run( self.__send_request(cmd ))

    # def device_set_schedule_rules(self, rules: str) -> Any:
    #     """Rules for schedule activation, e.g. 0000-0123456-on."""
    #     cmd = "settings/color/0"+ "?schedule="+str(int(state))
    #     return asyncio.run( self.__send_request(cmd ))


    def device_turn_on(self,timer: int = None) -> Any:
        """Turns on LED deveice.  Optional paramter specifies automatic flip-back timer in seconds (e.g. turned On or OFF for X seconds and will be switched back to previous state after that)"""
        cmd = "color/0?turn=on"
        if timer != None:
            cmd += "&timer="+str(timer)
        return asyncio.run( self.__send_request(cmd ))

    def device_turn_off(self) -> Any:
        """Turns off LED device"""
        cmd = "color/0?turn=off"
        return asyncio.run( self.__send_request(cmd ))


    def device_set_on_state(self,state: POWER_STATE,timer: int = None) -> Any:
        """Accepted values: on, off or toggle.  Optional paramter specifies automatic flip-back timer in seconds (e.g. turned On or OFF for X seconds and will be switched back to previous state after that)"""
        cmd = "color/0"+ "?turn="+str(state.value)
        if timer != None:
            cmd += "&timer="+str(timer)
        return asyncio.run( self.__send_request(cmd ))

    def device_set_one_shot_color_transition(self,delay: int) -> Any:
        """Set one-shot transition time between on/off and color change, [0-5000] ms."""
        cmd = "color/0"+ "?transition="+str(delay)
        return asyncio.run( self.__send_request(cmd ))

    def device_set_color(self,color: LED_COLOR ) -> Any:
        """Set the RGBW and brightness values."""
        cmd = "color/0?"
        joiner = ''
        if 0 <= color.red <= 255:
            cmd += joiner + "red="+str(color.red)
            joiner = '&'
        if 0 <= color.green <= 255:
            cmd += joiner + 'green='+str(color.green)
            joiner = '&'
        if 0 <= color.blue <= 255:
            cmd += joiner + 'blue='+str(color.blue)
            joiner = '&'
        if 0 <= color.white <= 255:
            cmd += joiner + 'white='+str(color.white)
            joiner = '&'
        if 0 <= color.brightness <= 100:
            cmd += joiner + 'gain='+str(color.brightness)
            joiner = '&'
        if color.on == 1:
            cmd += joiner + 'turn=on'
            joiner = '&'
        if color.on == 0:
            cmd += joiner + 'turn=off'
            joiner = '&'
        if color.timer != None:
            cmd += joiner + 'timer='+str(color.timer)
            joiner = '&'
        return asyncio.run( self.__send_request(cmd ))

    def device_on_with_color(self, red: int =None, green: int =None, blue: int =None, white: int =None, brightness: int =None, on: bool = None, timer: int = None) -> Any:
        color = LED_COLOR(red, green, blue, white, brightness, on, timer )
        return self.device_set_color(color)

    #
    # Private functions
    #
    async def __send_request( self, endpoint: str, data: Any = None, retry: int = 1 ) -> Any:
        """Send a request"""
        session = ClientSession(raise_for_status=True, timeout=EP_TIMEOUT )
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

        except ClientResponseError as err:
            if err.code == 401 and retry > 0:
                return await self.__send_request(endpoint, data, retry - 1)
            await session.close()
            raise
