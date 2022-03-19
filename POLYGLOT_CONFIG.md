# Shelly RGBW2 Configuration

This configuration is usually set automatically when the Nodeserver is started, or can be updated using the "Find Devices" button on the ISY Admin Console.  However, you can manually set the values if you wish to.

To manually add a device, use the Device ID found in the Settings->Device Info->DeviceID of the RGBW2 web page as the key, add the prefix "RGBW2_" to it, and use the IPV4 address as the value in a Custom Configuration Parameter of the Nodeserver Configuration.  For example if the device ID on the RGBW2 is 123ABC and it is at address 192.168.1.1, the custom parameter values are:
Key: RGBW2_123ABC
Value 192.168.1.1

If you remove a RGBW2 from your system, delete the corresponding name/address entry in the Custom Configuration Parameter area of the Nodeserver Configuration.

You can alos set logging level to debug using a custom configuration setting with a key of LOGGING and a value of DEBUG
