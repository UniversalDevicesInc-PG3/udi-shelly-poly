import enum
import json
from typing import Any
from ShellyDevice_Constants import *
from ShellyDevice_Base import *

class ShellyDevice_Shelly1(ShellyDevice_Base):
    """Controller class for the Shelly1 """

    def __init__(self, host: str, session: ClientSession = None):
        super().__init__( host, session)
        self.primary_output_channel  = 'relay/0'
        self.primary_status_channel = 'relays'

