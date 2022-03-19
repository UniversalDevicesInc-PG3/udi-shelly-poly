import polyinterface
import traceback

from  Node_Shared import *
from ShellyDevice_Shelly1 import ShellyDevice_Shelly1
from ShellyDevice_Base import DeviceConnectorError
from device_finder import Device_Finder


class Shelly1_Node(polyinterface.Node):
    """
    Class Variables:
    self.primary: String address of the Controller node.
    self.parent: Easy access to the Controller Class from the node itself.
    self.address: String address of this Node 14 character limit. (ISY limitation)
    self.added: Boolean Confirmed added to ISY
    """
    def __init__(self, controller, primary, isy_address, device_address, device_name):
        #You do NOT have to override the __init__ method, but if you do, you MUST call super.
        super(Shelly1_Node, self).__init__(controller, primary, isy_address, device_name)
        LOGGER.debug("Node: Init Node " + device_name + " ("+ device_address + ")")

        #set specific values
        self.device_addr = device_address
        self.queryON = True
        self.shelly_device = ShellyDevice_Shelly1(self.device_addr)

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
            # json_state =  self.shelly_device.get_device_status()
            # LOGGER.info('Node: status is  %s', json_state)
            # is_on = json_state[self.shelly_device.primary_status_channel][0]['ison']

            is_on = self.shelly_device.get_device_is_on()
            on_state = 0
            if is_on == True:
                on_state = 1

            LOGGER.debug('Node: Relay status = ' + str(is_on))

            self.setDriver('ST',    on_state )
            self.setDriver('GV19',  1)

        except DeviceConnectorError as ex :
            self.setDriver('GV19',  0)
            self.setDriver('ST',    0 )

        except Exception as ex :
            LOGGER.error('Node: updateStatuses: %s', str(ex))
            #LOGGER.error('Node: updateStatuses: %s', traceback.format_exc())

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

    def isOn(self) : 
        return self.shelly_device.get_device_is_on()
    
    drivers = [{'driver': 'ST',   'value': 0, 'uom': ISY_UOM_2_BOOL},    # Status = DevicePower On State
               {'driver': 'GV19', 'value': 0, 'uom': ISY_UOM_2_BOOL},      # Online/Offline
              ]  

    id = "Shelly1Device"
    #hint = '0x01040200'  #https://github.com/UniversalDevicesInc-PG3/udi-poly-ecobee/blob/7893dea2349b855d70a391347bd9130dde0e8804/nodes/Thermostat.py#L700
    hint = '0x02000000'  #https://wiki.universal-devices.com/index.php?title=Node_Hints_Documentation
    commands = {
                    'DON': on_DON,
                    'DOF': on_DOF,
                    'QUERY': On_Query,
                }

