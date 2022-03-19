import enum
import json
from typing import Any
from ShellyDevice_Constants import *
from ShellyDevice_Base import *



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


class ShellyDevice_RGBW2(ShellyDevice_Base):
    """Controller class for the Shelly_RGBW2 Color."""

    def __init__(self, host: str, user: str = None, pwd: str = None,session: ClientSession = None):
        super().__init__( host, user, pwd, session)
        """Initialize a Shelly_RGBW2_Client."""

        self.primary_output_channel  = 'color/0'
        self.primary_status_channel = 'lights'

    #
    # Device Information Funtions
    #
    def get_device_color_settings(self) -> Any:
            """Retrieve the device settings for color mode."""
            return asyncio.run( self._send_request( "settings/color/0"))

    def get_device_color_state(self) -> Any:
            """Retrieve the device settings for color mode."""
            return asyncio.run( self._send_request( "color/0"))

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
    def device_set_color_effect(self,effect: int) -> Any:
        """Set one of the effects from COLOR_EFFECT."""
        if not effect in range(0,4):
            return None
        cmd = "settings/color/0"+ "?effect="+str(effect)
        return asyncio.run( self._send_request(cmd ))

    def device_set_default_color_transition(self,delay: int) -> Any:
        """Set transition time between on/off and color change, [0-5000] ms."""
        cmd = "settings/color/0"+ "?transition="+str(delay)
        return asyncio.run( self._send_request(cmd ))

    def device_set_default_power_on_state(self,state: POWER_ON_STATE) -> Any:
        """Sets default power-on state: on, off or last"""
        cmd = "settings/color/0"+ "?default_state="+state.value
        return asyncio.run( self._send_request(cmd ))

    def device_set_power_auto_on_time(self,time: int) -> Any:
        """Sets a default timer to turn ON after every OFF command in seconds."""
        cmd = "settings/color/0"+ "?auto_on="+str(time)
        return asyncio.run( self._send_request(cmd ))

    def device_set_power_auto_off_time(self,time: int) -> Any:
        """Sets a default timer to turn OFF after every ON command in seconds."""
        cmd = "settings/color/0"+ "?auto_off="+str(time)
        return asyncio.run( self._send_request(cmd ))

    def device_set_button_type(self,type: BUTTON_INPUT_TYPE) -> Any:
        """Input type: momentary, toggle, edge, detached or action."""
        cmd = "settings/color/0"+ "?btn_type="+type.value
        return asyncio.run( self._send_request(cmd ))

    def device_set_button_invert_external_input(self,state: bool) -> Any:
        """Whether to invert external switch input."""
        cmd = "settings/color/0"+ "?btn_reverse="+str(int(state))
        return asyncio.run( self._send_request(cmd ))

    def device_set_schedule_enabled(self,state: bool) -> Any:
        """Enable or disable schedule timer."""
        cmd = "settings/color/0"+ "?schedule="+str(int(state))
        return asyncio.run( self._send_request(cmd ))

    def device_set_one_shot_color_transition(self,delay: int) -> Any:
        """Set one-shot transition time between on/off and color change, [0-5000] ms."""
        cmd = "color/0"+ "?transition="+str(delay)
        return asyncio.run( self._send_request(cmd ))

    def device_set_color(self,color: LED_COLOR ) -> Any:
        """Set the RGBW and brightness values."""
        cmd = "color/0?"
        joiner = ''
        if (color.red != None) and  (0 <= color.red <= 255):
            cmd += joiner + "red="+str(color.red)
            joiner = '&'
        if  (color.green != None) and  (0 <= color.green <= 255):
            cmd += joiner + 'green='+str(color.green)
            joiner = '&'
        if  (color.blue != None) and  (0 <= color.blue <= 255):
            cmd += joiner + 'blue='+str(color.blue)
            joiner = '&'
        if  (color.white != None) and  (0 <= color.white <= 255):
            cmd += joiner + 'white='+str(color.white)
            joiner = '&'
        if  (color.brightness != None) and  (0 <= color.brightness <= 100):
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
        return asyncio.run( self._send_request(cmd ))

    def device_on_with_color(self, red: int =None, green: int =None, blue: int =None, white: int =None, brightness: int =None, on: bool = None, timer: int = None) -> Any:
        color = LED_COLOR(red, green, blue, white, brightness, on, timer )
        return self.device_set_color(color)

