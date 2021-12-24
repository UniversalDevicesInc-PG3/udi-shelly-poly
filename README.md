# Shelly RGBW2 Polyglot V2 Node Server

This Nodeserver provides a basic interface between Shelly RGBW2 devices and Polyglot v3 server.

## Installation
This Nodeserver assumes the Shelly RGBW2 devices are already on your network, can be accessed via IPV4 address from the Polisy or whatever you use to run Polyglot and the devices are not using any form of authentication.

If no entries are not found in the custom configuration the NodeServer, it will  look for devices on the network at startup. The Nodeserver gives devices 5 seconds to respond to the discovery request, so this process may seem to take a while. Just be patient and slowly count to 5 :-)<br>

Shelly RGBW2 Device Setup
* The Shelly device must be on the same network as the ISY and Polyglot server
* The Shelly device must have an IPV4 address
* The Shelly device must be be set to be discoverable for the automatic discovery to work (default is to on, and the switch is found in settings on the device web page).

To manually add a device, use the Device ID found in the Settings->Device Info->DeviceID of the RGBW2 web page as the key, add the prefix "RGBW2_" to it, and use the IPV4 address as the value in a Custom Configuration Parameter of the Nodeserver Configuration.  For example if the device ID on the RGBW2 is 123ABC and it is at address 192.168.1.1, the custom parameter values are:
Key: RGBW2_123ABC
Value 192.168.1.1

If you remove a RGBW2 from your system, delete the corresponding name/address entry in the Custom Configuration Parameter area of the Nodeserver Configuration.

Shelly uses the MDNS protocol for finding the devices, but older firmware seems to be a little spotty on this.  Updating the firmware in the device to the latest version is suggested.  You do this via the system setting on the web server hosted on the device itself.<br>

These parameters should be found and entered automatically.

## Source
Shelly API at https://shelly-api-docs.shelly.cloud/gen1/#shelly-rgbw2-color<br>
UDI template at https://github.com/Einstein42/udi-poly-template-python

## Release Notes
0.0.1 - Just trying to get it to work!<br>
I have it automatically adding my configuration when installed.  This saves me a lot of time when developing, and for now I figure it gives you an example to start from.  **You will need to change this to work with your configuration.**  Developers who may be adding and removing the node frequently can tweak it by modifying the area commented as DEBUG CODE in the Shelly_RGBW2_Nodeserver.py file.  If you are not a developer, then you shouldn't need to remove the NodeServer frequently, and it won't matter :-)<br>

user/password on the Shelly is not supported right now, nor the Shelly button actions, nor the schedules.  This NodeServer primarily turns the LED strip on or off at the specified color settings.  I figure most of us will do the scheduling and programming though the ISY, not the Shelly.

It is kind of slow on updating status right now - it does it on the short poll.  You can change this short poll time to make it more responsive.  Meanwhile I will try to see if I can capture something from the device to make it event driven rather than polled.

The device will tell how much power it is using (in watts).  I'm not sure if this is useful in any way, but if you think it is let me know and I can make it available.<br><br>

0.0.2 - Just trying to get it to work, better!<br>
* Added the mDNS lookup to find devices.  It looks for devices if there is no config found on start, and I added a find button on the Admin console for use after some devices have been added.
* Programming clean up.  Shout-out to Bob Paauwe for the helpful suggestions.
