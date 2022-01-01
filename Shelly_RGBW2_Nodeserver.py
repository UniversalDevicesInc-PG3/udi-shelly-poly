#!/usr/bin/env python3

"""
This is a NodeServer for the Shelly RGBW written by TangoWhiskey1
"""
import polyinterface
import sys
import time
import logging
from copy import deepcopy
from types import BuiltinFunctionType
from typing import Any
from device_finder import Device_Finder

from ShellyDevice_RGBW2 import ShellyDevice_RGBW2
from ShellyDevice_Shelly1 import ShellyDevice_Shelly1
from Node_Shared import *
from RGBW2_Node import *
from Shelly1_Node import *

_MIN_IP_ADDR_LEN = 8

_NETWORK_DEVICE_IDS = { 
    'shellyrgbw2-' : 'RGBW2_' ,
    'shelly1-' :    'SHELLY1_'
    }

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

        #LOGGER.setLevel(logging.DEBUG)
        LOGGER.setLevel(logging.INFO)

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
        finder = Device_Finder( ['shellyrgbw2','shelly1']) 
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
                LOGGER.info('Checking if discovered device needs to be added to config: ' + cleaned_dev_name + ' ('+ ipAddr + ')')
                self.addCustomParam(  {cleaned_dev_name : ipAddr } )
                new_device_found = True
        self.removeNotice("ControllerAutoFind")
        return new_device_found

    def generate_name(self, network_device_name)->str:
        try:
            device_name = network_device_name[: network_device_name.index('-')+1]
            if device_name not in _NETWORK_DEVICE_IDS:
                return None
            return network_device_name.replace(device_name,_NETWORK_DEVICE_IDS[device_name] )
        except ValueError as ex:
            return None

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
                if device_name[:device_name.index('_')+1] not in _NETWORK_DEVICE_IDS.values():
                    LOGGER.error('Controller: Custom Params device name format incorrect. Must start with valid Shelly device type, instead found name of ' + device_name)
                    continue
                device_addr = config["customParams"][devName].strip()
                isy_addr = 's'+device_addr.replace(".","")
                if( len(isy_addr) < _MIN_IP_ADDR_LEN ):
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
                device_type = device_name[:device_name.index('_')] 

                if device_type == 'RGBW2':
                    self.addNode( RGBW2_Node(self, self.address, isy_addr,device_addr, device_name) )
                if device_type == 'SHELLY1':
                    self.addNode( Shelly1_Node(self, self.address, isy_addr,device_addr, device_name) )
           
    
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
    
    def on_discover(self,command):
        dev_found = self.auto_find_devices()
        if dev_found == True:
            self.process_config(self.polyConfig)

    id = 'RGBW2Controller'
    commands = { 
                'DISCOVER': on_discover,

    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': ISY_UOM_2_BOOL},  # Status
    ]

if __name__ == "__main__":
    try:
        poly = polyinterface.Interface('')
        poly.start()
        controller = RGBW2Controller(poly)
        controller.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
