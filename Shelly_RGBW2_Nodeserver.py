#!/usr/bin/env python3

"""
This is a NodeServer for the Shelly RGBW written by TangoWhiskey1
"""
import udi_interface
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

LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom

#
#
#  Controller Class
#
#
class RGBW2Controller(object):

    def __init__(self, polyglot):
        super(RGBW2Controller, self).__init__()
        self.poly = polyglot

        LOGGER.debug('Entered init')

        # implementation specific
        self.customParams = Custom(polyglot, 'customparams')
        self.device_nodes = dict()  #dictionary of ISY address to device Name and device IP address.
        self.configComplete = False

        polyglot.subscribe(polyglot.CUSTOMPARAMS, self.parameterHandler)
        polyglot.subscribe(polyglot.DISCOVER, self.on_discover)

        polyglot.setCustomParamsDoc()
        polyglot.updateProfile()

        polyglot.ready()
        self.start()

    def parameterHandler(self, params):
        self.poly.Notices.clear()
        self.configComplete = False

        if params and params != {}:
            for devName in params:
                device_name = devName.strip()
                if device_name[:device_name.index('_')+1] not in _NETWORK_DEVICE_IDS.values():
                    self.poly.Notices['bad_name'] = 'Custom Params device name format incorrect. Must start with valid Shelly device type, instead found name of ' + device_name
                    LOGGER.error('Controller: Custom Params device name format incorrect. Must start with valid Shelly device type, instead found name of ' + device_name)
                    continue

                device_addr = params[devName].strip()
                isy_addr = 's'+device_addr.replace(".","")
                if( len(isy_addr) < _MIN_IP_ADDR_LEN ):
                    self.poly.Notices['bad_ip'] = 'Custom Params device IP format incorrect. IP Address too short:' + isy_addr
                    LOGGER.error('Controller: Custom Params device IP format incorrect. IP Address too short:' + isy_addr)
                    continue

                self.device_nodes[isy_addr] = [device_name, device_addr]
                LOGGER.debug('Controller: Added device_node: ' + device_name + ' as isy address ' + isy_addr + ' (' + device_addr + ')')
            
            if len(self.device_nodes) == 0:
                LOGGER.error('Controller: No valid devices found in config, nothing to do!')
            else:
                self.configComplete = True
                self.add_devices()
        else:
            # No custom parameters, try auto discover
            self.auto_find_devices()
            if len(self.device_nodes) > 0:
                self.configComplete = True
                self.add_devices()

    def start(self):
        """
        This  runs once the NodeServer connects to Polyglot and gets it's config.
        No need to Super this method, the parent version does nothing.
        """        
        LOGGER.info('Controller: Started ShellyRGBW2 Node Server')

        # if stil no custom configuration, no devices found or given, so nothing to do
        while not self.configComplete:
            self.poly.Notices['missing'] = "ShellyRGBW2: Waiting for a valid user config"
            LOGGER.info('Waiting for a valid user config')
            time.sleep(5)

        self.poly.Notices.clear()

        # save devices to customParams (this will trigger handler)
        if len(self.device_nodes) > 0:
            for dev in self.device_nodes:
                self.customParams[self.device_nodes[dev][0]] = self.device_nodes[dev][1]
                


    def auto_find_devices(self) -> bool:
        self.poly.Notices['auto'] = "Looking for devices on network, this will take few seconds"
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

            isy_addr = 's'+ipAddr.replace(".","")
            self.device_nodes[isy_addr] = [cleaned_dev_name, ipAddr]
            new_device_found = True

        self.poly.Notices.delete('auto')
        return new_device_found

    def generate_name(self, network_device_name)->str:
        try:
            device_name = network_device_name[: network_device_name.index('-')+1]
            if device_name not in _NETWORK_DEVICE_IDS:
                return None
            return network_device_name.replace(device_name,_NETWORK_DEVICE_IDS[device_name] )
        except ValueError as ex:
            return None

    def add_devices(self):
        LOGGER.debug('Controller: add_devices called')
        for isy_addr in self.device_nodes.keys():
            if not self.poly.getNode(isy_addr):
                device_name = self.device_nodes[isy_addr][0]
                device_addr = self.device_nodes[isy_addr][1]
                device_type = device_name[:device_name.index('_')] 

                if device_type == 'RGBW2':
                    self.poly.addNode( RGBW2_Node(self.poly, isy_addr, isy_addr, device_addr, device_name) )
                if device_type == 'SHELLY1':
                    self.poly.addNode( Shelly1_Node(self.poly, isy_addr, isy_addr, device_addr, device_name) )
           
    
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

    def delete(self):
        """
        This is sent by Polyglot upon deletion of the NodeServer. If the process is
        co-resident and controlled by Polyglot, it will be terminiated within 5 seconds
        of receiving this message.
        """
        LOGGER.info('Controller: Deleting The ShellyRGBW2 Nodeserver')

    
    def on_discover(self):
        dev_found = self.auto_find_devices()

        # save devices to customParams (will trigger handler)
        if len(self.device_nodes) > 0:
            for dev in self.device_nodes:
                self.customParams[self.device_nodes[dev][0]] = self.device_nodes[dev][1]

    id = 'RGBW2Controller'

if __name__ == "__main__":
    try:
        poly = udi_interface.Interface([])
        poly.start('2.0.0')
        RGBW2Controller(poly)
        poly.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
