# Shelly RGBW2 Polyglot V2 Node Server

This Nodeserver provides a basic interface between Shelly RGBW2 devices and Polyglot v3 server.

## Installation
This Nodeserver assumes the Shelly RGBW2 devices are already on your network, can be accessed via IPV4 address from the Polisy or whatever you use to run Polyglot, you know that IP address, and the devices are not using any form of authentication.

Required custom config values are:<br>
 &ensp;* Number of nodes (devices):<br>
 &emsp;&emsp;Key: Num_RGBW2<br>
 &emsp;&emsp;Value:The number of Shelly RGBW2 nodes to add<br>
* Name and Address for each of the devices<br>
&emsp;&emsp;Key:  RGBW2_#, where # is the node number and starts at 1<br>
&emsp;&emsp;Value: Device name, IPV4 address of device<br>
&emsp;&emsp;(e.g., Shelly 1, 192,168.0.100).<br>
The number of Name/Address parameters should equal the value in Num_RGBW2

## Source
Shelly API at https://shelly-api-docs.shelly.cloud/gen1/#shelly-rgbw2-color<br>
UDI template at https://github.com/Einstein42/udi-poly-template-python

## Release Notes
0.0.1 - Just trying to get it to work!<br>
I have it automatically adding my configuration when installed.  This saves me a lot of time when developing, and for now I figure it gives you an example to start from.  **You will need to change this to work with your configuration.**  Developers who may be adding and removing the node frequently can tweak it by modifying the area commented as DEBUG CODE in the Shelly_RGBW2_Nodeserver.py file.  If you are not a developer, then you shouldn't need to remove the NodeServer frequently, and it won't matter :-)<br>

user/password on the Shelly is not supported right now, nor the Shelly button actions, nor the schedules.  This NodeServer primarily turns the LED strip on or off at the specified color settings.  I figure most of us will do the scheduling and programming though the ISY, not the Shelly.

It is kind of slow on updating status right now - it does it on the short poll.  You can change this short poll time to make it more responsive.  Meanwhile I will try to see if I can capture something from the device to make it event driven rather than polled.

The device will tell how much power it is using (in watts).  I'm not sure if this is useful in any way, but if you think it is let me know and I can  make it available.
