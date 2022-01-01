#
#
#  RGBW2 Node Class
#
#

import polyinterface
from ShellyDevice_RGBW2 import ShellyDevice_RGBW2
from  Node_Shared import *
from device_finder import Device_Finder


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
        self.shelly_device = ShellyDevice_RGBW2(self.device_addr)

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
    
    drivers = [{'driver': 'ST',   'value': 0, 'uom': ISY_UOM_2_BOOL},    # Status = LED Strip Power On State
               {'driver': 'GV10', 'value': 0, 'uom': ISY_UOM_100_BYTE},  # Red
               {'driver': 'GV11', 'value': 0, 'uom': ISY_UOM_100_BYTE},  # Green 
               {'driver': 'GV12', 'value': 0, 'uom': ISY_UOM_100_BYTE},  # Blue
               {'driver': 'GV13', 'value': 0, 'uom': ISY_UOM_100_BYTE},  # White
               {'driver': 'GV14', 'value': 0, 'uom': ISY_UOM_78_0TO100_ONOFF},   # Brightness 
               {'driver': 'GV15', 'value': 0, 'uom': ISY_UOM_42_MILLISECOND},   # Timer
               {'driver': 'GV16', 'value': 0, 'uom': ISY_UOM_2_BOOL},      # On/Off
               {'driver': 'GV17', 'value': 0, 'uom': ISY_UOM_42_MILLISECOND},      # Transition Time
               {'driver': 'GV18', 'value': 0, 'uom': ISY_UOM_25_INDEX},      # Effect
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

