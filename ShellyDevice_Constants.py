import enum
from typing import Any
    
class POWER_STATE(enum.Enum):
    """Power On States supported by Shelly1 API."""
    Off            = "off"
    On             = "on"
    Toggle         = "toggle"

class BUTTON_INPUT_TYPE(enum.Enum):
    """List of Button Input Types supported by Shelly_RGBW2_Client API."""
    Momentary = "momentary"
    Toggle    = "toggle"
    Edge      = "edge"
    Detached  = "detached"
    Action    = "action"

class POWER_ON_STATE(enum.Enum):
    """Power On States supported by Shelly_RGBW2_Client API."""
    Off            = "off"
    On             = "on"
    Last           = "last"

