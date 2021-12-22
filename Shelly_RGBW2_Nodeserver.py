#!/usr/bin/env python3

"""
This is a NodeServer for the Shelly RGBW written by TangoWhiskey1
"""

import polyinterface
from Shelly_RGBW2_Client import Shelly_RGBW2_Client
import json
import sys
import logging
import warnings 
import urllib3
from copy import deepcopy
from types import BuiltinFunctionType
from typing import Any

LOGGER = polyinterface.LOGGER

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


_PARM_NUM_DEVICES_NAME = "Num_RGBW2"
_PART_ADDR_FORMAT_STRING = "RGBW2_{}"

"""
def get_profile_info(logger):
    pvf = 'profile/version.txt'
    try:
        with open(pvf) as f:
            pv = f.read().replace('\n', '')
    except Exception as err:
        logger.error('get_profile_info: failed to read  file {0}: {1}'.format(pvf,err), exc_info=True)
        pv = 0
    f.close()
    return { 'version': pv }
"""
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
        self.name = 'Shelly RGBW2 Controller'
        self.hb = 0 #heartbeat
        self.poly = polyglot
        self.queryON = True

        LOGGER.setLevel(logging.DEBUG)
        LOGGER.debug('Entered init')

        # implementation specific
        self.numDevices = 0
        self.device_nodes = dict()  #dictionary of ISY address to device Name and device IP address.
        self.configComplete = False

        polyglot.addNode(self)  #add this controller node first

    def start(self):
        """
        This  runs once the NodeServer connects to Polyglot and gets it's config.
        No need to Super this method, the parent version does nothing.
        """        
        LOGGER.info('Controller: Started Shelly RGBW2 Node Server for v3 NodeServer ')
        # Show values on startup if desired.
        LOGGER.debug('ST=%s',self.getDriver('ST'))
        self.setDriver('ST', 1)
        self.heartbeat(0)

        #####################
        #  DEBUG CODE #######
        #####################
        if self.getCustomParam(_PARM_NUM_DEVICES_NAME) == None:
            LOGGER.debug('***Adding custom config***')
            self.addCustomParam( {"Num_RGBW2": "3"} )
            self.addCustomParam( {"RGBW2_1":"Shelly1, 192.168.3.64"} )
            self.addCustomParam( {"RGBW2_2":"Shelly2, 192.168.3.65"} )
            self.addCustomParam( {"RGBW2_3":"Shelly3, 192.168.3.66"} )
        #####################
        #####################
        #####################

        self.process_config(self.polyConfig)
        
        # if no custom configuration, no devices given, so nothing to do
        if not self.configComplete:
            LOGGER.error('Controller: ** Invalid configuation found! Shutting down node server')
            self.poly.send({"stop": {}})
            return

        # Set the nodeserver status flag to indicate nodeserver is running
        self.setDriver("ST", 1, True, True)



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

            self.numDevices = int(self.getCustomParam(_PARM_NUM_DEVICES_NAME))

            if self.numDevices == None:
                LOGGER.error('Controller: Num Devices custom parameter not found')
                return
            
            if self.numDevices == 0:
                LOGGER.error('Controller: Num Devices is zero, nothing to do')
                return

            LOGGER.debug('Controller: Parsing Custom Params')
            for num in range(self.numDevices):
                device_config_str =self.getCustomParam( _PART_ADDR_FORMAT_STRING.format(num+1))
                if device_config_str == None:
                    LOGGER.error('Controller: Can not find device string for device number ' + str(num+1))
                    return

                device_config_str = device_config_str.split(",") 
                device_name = device_config_str[0].strip()

                device_addr = device_config_str[1].strip()
                isy_addr = 's'+device_addr.replace(".","")

                self.device_nodes[isy_addr] = [device_name, device_addr]
                LOGGER.debug('Controller: Added device_node: ' + device_name + 'as isy address ' + isy_addr + ' (' + device_addr + ')')
            self.configComplete = True
            self.add_devices()
        except Exception as ex:
            LOGGER.error('Controller: Error parsing config in the Shelly RGBW2 NodeServer: %s', str(ex))


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
        LOGGER.info('Controller: Deleting The Shelly RGBW2 Nodeserver')

    def set_module_logs(self,level):
        logging.getLogger('urllib3').setLevel(level)

    def update_profile(self,command):
        LOGGER.debug('Controller: update_profile called')
        st = self.poly.installprofile()
        return st

    id = 'RGBW2Controller'
    commands = { }
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
        LOGGER.debug('shortPoll')
        self.updateStatuses()

    def updateStatuses(self):
        LOGGER.debug('Node: updateStatuses() called for  %s (%s)', self.name, self.address)
        try :
            device_color = self.shelly_device.get_device_color()
            on_state = 0
            if device_color.on == True:
                on_state = 1
            LOGGER.debug('Node: LED status = [%s, %s, %s, %s]', str(on_state), str(device_color.red), str(device_color.green), str(device_color.blue)  )

            self.setDriver('ST',    on_state )
            self.setDriver('GV10',  device_color.red)
            self.setDriver('GV11',  device_color.green)
            self.setDriver('GV12',  device_color.blue)
            self.setDriver('GV13',  device_color.white)
            self.setDriver('GV14',  device_color.brightness)
            self.setDriver('GV15',  device_color.timer)
            self.setDriver('GV16',  on_state)
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
    
    def On_BRT(self, command):
        LOGGER.debug('Node: On_BRT() called')
        try:
            gain = int(command.get('value'))
            self.shelly_device.device_on_with_color(brightness=gain)
            self.updateStatuses()
        except Exception as ex:
            LOGGER.error('On_BRT: %s', str(ex))
        
    def On_Query(self, command):
        LOGGER.debug('Node: On_Query() called')
        self.updateStatuses()

    def On_SetColor(self, command):
        LOGGER.debug('Node: On_SetColor() called')
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

    
    def On_SetEffect(self, command):
        LOGGER.debug('Node: On_SetEffect() called')
        query  = command.get('query')
        eff_num  = int(query.get('EFF.uom25'))
        self.shelly_device.device_set_color_effect(eff_num)
        self.updateStatuses()
        pass

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
              ]  

    id = "RGBW2Device"
    commands = {
                    'DON': on_DON,
                    'DOF': on_DOF,
                    'BRT': On_BRT,
                    'Query': On_Query,
                    'SET_COLOR_RGBW': On_SetColor,
                    'SET_EFFECT': On_SetEffect,
                }


if __name__ == "__main__":
    try:
        poly = polyinterface.Interface([])
        poly.start()
        controller = RGBW2Controller(poly)
        controller.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
