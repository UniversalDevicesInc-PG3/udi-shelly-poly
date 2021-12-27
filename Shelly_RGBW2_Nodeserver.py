#!/usr/bin/env python3

"""
This is a NodeServer for the Shelly RGBW written by TangoWhiskey1
"""

import polyinterface
from Shelly_RGBW2_Client import Shelly_RGBW2_Client
import json
import sys
import time
import logging
import warnings 
import urllib3
from copy import deepcopy
from types import BuiltinFunctionType
from typing import Any
from device_finder import Device_Finder

LOGGER = polyinterface.LOGGER
#_Logging_level = logging.DEBUG
_Logging_level = logging.INFO


# constants for ISY Nodeserver interface
_ISY_UOM_2_BOOL = 2 
_ISY_UOM_25_INDEX = 25 
_ISY_UOM_42_MILLISECOND = 42
_ISY_UOM_56_RAW = 56 
_ISY_UOM_58_SECONDS = 58 
_ISY_UOM_70_USER = 70
_ISY_UOM_73_WATT = 73 
_ISY_UOM_78_0TO100_ONOFF = 78 
_ISY_UOM_100_BYTE = 100


_PART_NAME_PREFIX = "RGBW2_"

#
#
#  Controller Class
#
#
class RGBW2Controller(polyinterface.Controller):

    def __init__(self, polyglot):
        """
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.

         Class Variables:
        self.nodes: Dictionary of nodes. Includes the Controller node. Keys are the node addresses
        self.name: String name of the node
        self.address: String Address of Node, must be less than 14 characters (ISY limitation)
        self.polyConfig: Full JSON config dictionary received from Polyglot for the controller Node
        self.added: Boolean Confirmed added to ISY as primary node
        self.config: Dictionary, this node's Config
        """
        super(RGBW2Controller, self).__init__(polyglot)
        # ISY required
        self.name = 'ShellyRGBWController'
        self.hb = 0 #heartbeat
        self.poly = polyglot
        self.queryON = True

        LOGGER.setLevel(_Logging_level)
        LOGGER.debug('Entered init')

        # implementation specific
        self.device_nodes = dict()  #dictionary of ISY address to device Name and device IP address.
        self.configComplete = False

        polyglot.addNode(self)  #add this controller node first

    def start(self):
        """
        This  runs once the NodeServer connects to Polyglot and gets it's config.
        No need to Super this method, the parent version does nothing.
        """        
        LOGGER.info('Controller: Started ShellyRGBW2 Node Server for v2 NodeServer ')
        self.server_data = self.poly.get_server_data(check_profile=True)

        # Show values on startup if desired.
        LOGGER.debug('ST=%s',self.getDriver('ST'))
        self.setDriver('ST', 1)
        self.heartbeat(0)
        
        #  Auto Find devices if nothing in config
        if (self.polyConfig["customParams"] == None) or (len(self.polyConfig["customParams"]) == 0):
            self.auto_find_devices()

        self.process_config(self.polyConfig)
        
        # if stil no custom configuration, no devices found or given, so nothing to do
        while not self.configComplete:
            self.addNotice({"WaitingForConfig":"ShellyRGBW2: Waiting for a valid user config"})
            LOGGER.info('Waiting for a valid user config')
            time.sleep(5)
            self.removeNotice("WaitingForConfig")

        # Set the nodeserver status flag to indicate nodeserver is running
        self.setDriver("ST", 1, True, True)


    def auto_find_devices(self) -> bool:
        self.addNotice({"ControllerAutoFind":"ShellyRGBW2: Looking for devices on network, this will take few seconds"})
        new_device_found = False
        finder = Device_Finder( 'shellyrgbw2')
        finder.look_for_devices()
        LOGGER.info( "Controller: Found " + str(len(finder.devices)) + " devices:" )
        for devName in finder.devices:
            ipAddr = finder.devices[devName][:-3] #remove the port number from the address
            cleaned_dev_name = self.generate_name(devName)
            if( cleaned_dev_name == None):
                LOGGER.error('Controller: Invalid name for device found in config, device not added: ' + devName )
                continue
            #See if device exists, if  not add
            if( self.getCustomParam(cleaned_dev_name) == None ):
                LOGGER.info('Adding discovered device to config: ' + cleaned_dev_name + ' ('+ ipAddr + ')')
                self.addCustomParam(  {cleaned_dev_name : ipAddr } )
                new_device_found = True
        self.removeNotice("ControllerAutoFind")
        return new_device_found

    def generate_name(self, network_device_name)->str:
        if (network_device_name[:12] != 'shellyrgbw2-') or (len(network_device_name) < 17):
            return None
        return _PART_NAME_PREFIX + network_device_name[12:18]

    def process_config(self, config):
        self.removeNoticesAll()
        LOGGER.debug('process_config called')
        LOGGER.debug(config)
        try:
            if config == None:
                LOGGER.error('Controller: Poly config not found')
                return

            if config["customParams"] == None:
                LOGGER.error('Controller: customParams not found in Config')
                return

            for devName in config["customParams"]:
                device_name = devName.strip()
                if( device_name[:len(_PART_NAME_PREFIX)] != _PART_NAME_PREFIX):
                    LOGGER.error('Controller: Custom Params device name format incorrect. Must start with '+ _PART_NAME_PREFIX + '  found name of ' + device_name)
                    continue
                device_addr = config["customParams"][devName].strip()
                isy_addr = 's'+device_addr.replace(".","")
                if( len(isy_addr) < 8 ):
                    LOGGER.error('Controller: Custom Params device IP format incorrect. IP Address too short:' + isy_addr)
                    continue
                self.device_nodes[isy_addr] = [device_name, device_addr]
                LOGGER.debug('Controller: Added device_node: ' + device_name + ' as isy address ' + isy_addr + ' (' + device_addr + ')')
            
            if len(self.device_nodes) == 0:
                LOGGER.error('Controller: No devices found in config, nothing to do!')
                return
            self.configComplete = True
            self.add_devices()
        except Exception as ex:
            LOGGER.error('Controller: Error parsing config in the ShellyRGBW2 NodeServer: %s', str(ex))

    def add_devices(self):
        LOGGER.debug('Controller: add_devices called')
        for isy_addr in self.device_nodes.keys():
            if not isy_addr in self.nodes:
                device_name = self.device_nodes[isy_addr][0]
                device_addr = self.device_nodes[isy_addr][1]
                self.addNode( RGBW2_Node(self, self.address, isy_addr,device_addr, device_name) )
           
    
    def shortPoll(self):
        """
        This runs every 10 seconds. You would probably update your nodes either here
        or longPoll. No need to Super this method the parent version does nothing.
        The timer can be overriden in the server.json.
        """
        LOGGER.debug('Controller: shortPoll called')
        self.setDriver('ST',  1)
        for node in self.nodes:
            if node != self.address:
                self.nodes[node].shortPoll()

    def longPoll(self):
        LOGGER.debug('Controller: longPoll')
        self.heartbeat()
        
    def heartbeat(self,init=False):
        LOGGER.debug('Controller: heartbeat: init={}'.format(init))
        if init is not False:
            self.hb = init
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def delete(self):
        """
        This is sent by Polyglot upon deletion of the NodeServer. If the process is
        co-resident and controlled by Polyglot, it will be terminiated within 5 seconds
        of receiving this message.
        """
        LOGGER.info('Controller: Deleting The ShellyRGBW2 Nodeserver')

    def set_module_logs(self,level):
        logging.getLogger('urllib3').setLevel(level)

    def update_profile(self,command):
        LOGGER.debug('Controller: update_profile called')
        st = self.poly.installprofile()
        return st
    
    def on_discover(self):
        dev_found = self.auto_find_devices()
        if dev_found == True:
            self.process_config(self.polyConfig)

    id = 'RGBW2Controller'
    commands = { 
                'DISCOVER': on_discover,

    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': _ISY_UOM_2_BOOL},  # Status
    ]



#
#
#  Node Class
#
#
class RGBW2_Node(polyinterface.Node):
    """
    Class Variables:
    self.primary: String address of the Controller node.
    self.parent: Easy access to the Controller Class from the node itself.
    self.address: String address of this Node 14 character limit. (ISY limitation)
    self.added: Boolean Confirmed added to ISY
    """
    def __init__(self, controller, primary, isy_address, device_address, device_name):
        #You do NOT have to override the __init__ method, but if you do, you MUST call super.
        super(RGBW2_Node, self).__init__(controller, primary, isy_address, device_name)
        LOGGER.debug("Node: Init Node " + device_name + " ("+ device_address + ")")

        #set specific values
        self.device_addr = device_address
        self.queryON = True
        self.shelly_device = Shelly_RGBW2_Client(self.device_addr)

    def start(self):
        """
        This method is run once the Node is successfully added to the ISY
        and we get a return result from Polyglot. Only happens once.
        """
        LOGGER.debug('Node: Start called for node ' + self.name + ' (' + self.address + ')')
        self.updateStatuses() 

    def shortPoll(self):
        self.updateStatuses()

    def updateStatuses(self):
        LOGGER.debug('Node: updateStatuses() called for  %s (%s)', self.name, self.address)
        try :
            device_status = self.shelly_device.get_device_settings()
            red        = device_status['lights'][0]['red']
            green      = device_status['lights'][0]['green']
            blue       = device_status['lights'][0]['blue']
            white      = device_status['lights'][0]['white']
            brightness = device_status['lights'][0]['gain']
            is_on       = device_status['lights'][0]['ison']
            transition = device_status['lights'][0]['transition']
            effect     = device_status['lights'][0]['effect']
            on_state = 0
            if is_on == True:
                on_state = 1

            LOGGER.debug('Node: LED status = RGBWBr[%s, %s, %s, %s, %s] - OTE[%s, %s, %s]', str(red), str(green), str(blue) ,str(white),str(brightness),str(is_on),str(transition),str(effect))

            self.setDriver('ST',    on_state )
            self.setDriver('GV10',  red)
            self.setDriver('GV11',  green)
            self.setDriver('GV12',  blue)
            self.setDriver('GV13',  white)
            self.setDriver('GV14',  brightness)
            self.setDriver('GV16',  on_state)
            self.setDriver('GV17',  transition) 
            self.setDriver('GV18',  effect) 

        except Exception as ex :
            LOGGER.error('Node: updateStatuses: %s', str(ex))

    def on_DON(self, command):
        LOGGER.debug('Node: on_DON() called')
        try:
            self.shelly_device.device_turn_on()
            self.updateStatuses()
        except Exception as ex:
            LOGGER.error('Node: on_DON: %s', str(ex))
        
    def on_DOF(self, command):
        LOGGER.debug('Node: on_DOF() called')
        try :
            self.shelly_device.device_turn_off()
            self.updateStatuses()
        except Exception as ex:
            LOGGER.error('on_DOF: %s', str(ex))
    
    def On_Query(self, command):
        LOGGER.debug('Node: On_Query() called')
        self.updateStatuses()

    def On_SetAllColor(self, command):
        LOGGER.debug('Node: On_SetAllColor() called')
        try:
            query  = command.get('query')
            r_cmd  = int(query.get('R.uom100'))
            g_cmd  = int(query.get('G.uom100'))
            b_cmd  = int(query.get('B.uom100'))
            w_cmd  = int(query.get('W.uom100'))
            br_cmd = int(query.get('BR.uom78'))
            on_cmd = int(query.get('ON.uom2'))
            timer_cmd  = int(query.get('TM.uom42'))
            
            on_state = False
            if on_cmd == 1:
                on_state = True

            self.shelly_device.device_on_with_color(red = r_cmd, green = g_cmd, blue = b_cmd, white = w_cmd, brightness = br_cmd, timer = timer_cmd, on=on_state)
            self.updateStatuses()
        except Exception as ex:
            LOGGER.error('On_SetColor: %s', str(ex))

    def On_SetColor(self, command):
        LOGGER.debug('Node: On_SetAllColor() called')
        try:
            query  = command.get('query')
            r_cmd  = int(query.get('RSC.uom100'))
            g_cmd  = int(query.get('GSC.uom100'))
            b_cmd  = int(query.get('BSC.uom100'))
            w_cmd  = int(query.get('WSC.uom100'))
            self.shelly_device.device_on_with_color(red = r_cmd, green = g_cmd, blue = b_cmd, white = w_cmd)
            self.updateStatuses()
        except Exception as ex:
            LOGGER.error('On_SetAllColor: %s', str(ex))

    def On_Brightness(self, command):
        try:
            query  = command.get('query')
            gain  = int(query.get('BRSB.uom78'))
            self.shelly_device.device_on_with_color(brightness=gain)
            self.updateStatuses()
        except Exception as ex:
            LOGGER.error('On_BRT: %s', str(ex))

    
    def On_SetEffect(self, command):
        LOGGER.debug('Node: On_SetEffect() called')
        query  = command.get('query')
        eff_num  = int(query.get('EFF.uom25'))
        self.shelly_device.device_set_color_effect(eff_num)
        self.updateStatuses()

    def On_SetTransition(self, command):
        LOGGER.debug('Node: On_SetTransition() called')
        query  = command.get('query')
        eff_num  = int(query.get('TRN.uom42'))
        self.shelly_device.device_set_default_color_transition(eff_num)
        self.updateStatuses()

    def isOn(self) : 
        return self.shelly_device.get_device_is_on()
        
    def getBri(self) : 
        device_color = self.shelly_device.get_device_color()
        return device_color.brightness
    
    drivers = [{'driver': 'ST',   'value': 0, 'uom': _ISY_UOM_2_BOOL},    # Status = LED Strip Power On State
               {'driver': 'GV10', 'value': 0, 'uom': _ISY_UOM_100_BYTE},  # Red
               {'driver': 'GV11', 'value': 0, 'uom': _ISY_UOM_100_BYTE},  # Green 
               {'driver': 'GV12', 'value': 0, 'uom': _ISY_UOM_100_BYTE},  # Blue
               {'driver': 'GV13', 'value': 0, 'uom': _ISY_UOM_100_BYTE},  # White
               {'driver': 'GV14', 'value': 0, 'uom': _ISY_UOM_78_0TO100_ONOFF},   # Brightness 
               {'driver': 'GV15', 'value': 0, 'uom': _ISY_UOM_42_MILLISECOND},   # Timer
               {'driver': 'GV16', 'value': 0, 'uom': _ISY_UOM_2_BOOL},      # On/Off
               {'driver': 'GV17', 'value': 0, 'uom': _ISY_UOM_42_MILLISECOND},      # Transition Time
               {'driver': 'GV18', 'value': 0, 'uom': _ISY_UOM_25_INDEX},      # Effect
              ]  

    id = "RGBW2Device"
    commands = {
                    'DON': on_DON,
                    'DOF': on_DOF,
                    'QUERY': On_Query,
                    'SET_ALL_COLOR': On_SetAllColor,
                    'SET_COLOR_RGBW': On_SetColor,
                    'SET_BRIGHTNESS': On_Brightness,
                    'SET_TRANSITION': On_SetTransition,
                    'SET_EFFECT': On_SetEffect,
                }


if __name__ == "__main__":
    try:
        poly = polyinterface.Interface('')
        poly.start()
        controller = RGBW2Controller(poly)
        controller.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
