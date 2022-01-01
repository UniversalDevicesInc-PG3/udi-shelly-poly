# Shelly RGBW2 Polyglot V2 Node Server

This Nodeserver provides a basic interface between Shelly RGBW2 and Shelly1 devices and Polyglot v2 server.

## Installation
This Nodeserver assumes the Shelly  devices are already on your network, can be accessed via IPV4 address from the Polisy or whatever you use to run Polyglot and the devices are not using any form of authentication.

If there are no entries in the custom configuration the NodeServer, it will  look for devices on the network at startup. The Nodeserver gives devices 5 seconds to respond to the discovery request, so this process may seem to take a while. Just be patient and slowly count to 5 :-)<br>

### Shelly  Device Setup
* The Shelly device must be on the same network as the ISY and Polyglot server
* The Shelly device must have an IPV4 address
* The Shelly device must be be set to be discoverable for the automatic discovery to work (default is to on, and the switch is found in settings on the device web page).

To manually add a device, use the Device ID found in the Settings->Device Info->DeviceID of the device web page as the key, add the device prefix ("RGBW2_" or "Shelly1_") to it, and use the IPV4 address as the value in a Custom Configuration Parameter of the Nodeserver Configuration.  For example if the device ID of a RGBW2 is 123ABC and it is at IP address 192.168.1.1, the custom parameter values are:<br>
Key: RGBW2_123ABC<br>
Value 192.168.1.1<br>
<br>
To remove a device from your system, delete the corresponding name/address entry in the Custom Configuration Parameter area of the Nodeserver Configuration.
<br>
Shelly uses the MDNS protocol for finding the devices, but older firmware seems to be a little spotty on this.  Updating the firmware in the device to the latest version is suggested.  You do this via the system setting on the web server hosted on the device itself.<br>

These parameters should be found and entered automatically.

## Misc
The devices update their status on the Nodeserver's short poll.  You can change this short poll time to make it more responsive in the NodeServer Configuration.

## Source
Shelly API at https://shelly-api-docs.shelly.cloud/gen1/#shelly-rgbw2-color<br>
UDI template at https://github.com/Einstein42/udi-poly-template-python

## Release Notes
0.0.1 - Just trying to get it to work!<br>
* I have it automatically adding my configuration when installed.  This saves me a lot of time when developing, and for now I figure it gives you an example to start from.  You will need to change this to work with your configuration.  Developers who may be adding and removing the node frequently can tweak it by modifying the area commented as DEBUG CODE in the Shelly_RGBW2_Nodeserver.py file.  If you are not a developer, then you shouldn't need to remove the NodeServer frequently, and it won't matter<br>

--------

0.0.2 - Auto discovery of Shelly devices<br>
* Added the mDNS lookup to find devices.  It looks for devices if there is no config found on start, and I added a find button on the Admin console for use after some devices have been added.
* Programming clean up.  Shout-out to Bob Paauwe for the helpful suggestions.

--------

0.0.3 - More features<br>
* Separated several commands to make programming more granular. Now you can set the all the color settings at once, or set RGBW, and Brightness separately.
* Added the transition time.  This is the time the LED take to get up to the set brightness.  This setting can have a dramatic effect if you are doing ramps using programming.  It seems to work best if the transition time is shorter than the program ramp rate.  THe default in the device is 1000ms, and the timer in ISY work on seconds, so there can be a race condition.
* Added the effect to the status window so you can see if it is on. Effect settings override whatever you set the device to,so if some program leaves them on you can get unexpected color shifts when you turn on the LEDs.
* Added a Query button which forces the device to update all the statuses.
* Added the parameters to the string shown in programming and scenes to make it easier to see what you have done

--------

1.0.0 - Shelly 1 Support<br>
* Refactored the files to make it easier to add new types of devices.
* Added basic on/off support for the Shelly1 relay
* Looked into ColoT and MQTT interfaces and decided not so go with it, at least for now on these devices.  Both send status on a schedule, which gives the the same result as polling on the same schedule.  Using them would result in less network traffic, but it really isn't all that much traffic with the REST interface and the gain does not seem worth the programming effort.
