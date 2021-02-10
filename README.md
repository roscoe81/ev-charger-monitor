# ev-charger-monitor
Remotely monitors and controls a Mercedes-Benz Wallbox Home EV Charger via The Things Network(TTN) LoRaWAN.

## System Overview
![System Overview](https://github.com/roscoe81/ev-charger-monitor/blob/main/Documentation/Northcliff%20EV%20Charger%20Monitor%20Overview.png).

This monitor allows [Home Manager](https://github.com/roscoe81/Home-Manager) to interwork with an EV charger over LoRaWAN via The Things Network. It can monitor the state of the EV charger, as well as performing lock outlet, unlock outlet and reset charger commands (* See note about downlink command timing). The Things Network is used to support charger locations that aren't able to provide wifi coverage (e.g. in a basement garage). It requires customised TTN payload formats that can be found [here](https://github.com/roscoe81/ev-charger-monitor/tree/main/TTN%20Payload%20Formats) and the setup of a mosquitto bridge on the Home Manager side of the system.

* Note that the TTN functionality provides timely uplinking of charger state data, but downlink data (i.e. commands to the charger) are only sent after an uplink message. Therefore commands to the charger are not sent immediately and will be delayed. This does impact the functionality, but it's been minimised by varying the loop timings, based on the charger state.

## Hardware
![Hardware](https://github.com/roscoe81/ev-charger-monitor/blob/main/Photos/IMG_5237.jpg)
The [monitor](https://github.com/roscoe81/ev-charger-monitor/tree/main/Photos) uses a Pycom LoPy4, Pycom Expansion Board 3.0 and a Sparkfun BOB-10124 Transceiver Breakout for RS485 Modbus communications(P3 to RX-1, P4 to TX-0 and P8 to RTS)

**Be aware that this project should only be constructed and deployed by a licenced electrician and its use might void charger and vehicle warranties. See LICENCE.md for disclaimers.**

## License
This project is licensed under the MIT License - see the LICENSE.md file for details

## Acknowledgements
The project has used some of the charger interworking functionality in https://github.com/cvvmedia/symcon.cvvmedia.ablchargepoint. That functionality, combined with my additional protocol analyis is [here](https://github.com/roscoe81/ev-charger-monitor/blob/main/Documentation/Charger%20Protocol.pdf).



