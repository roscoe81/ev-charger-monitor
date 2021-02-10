# ev-charger-monitor
Remotely monitors and controls a Mercedes-Benz Wallbox Home EV Charger via The Things Network(TTN) LoRaWAN. It can be used to reduce EV running costs by automatically starting and monitoring EV charging during times when off-peak electricity rates are in place and where the EV does not support time-based charging triggers.

## System Overview
![System Overview]https://github.com/roscoe81/ev-charger-monitor/blob/main/Documentation/Northcliff%20EV%20Charger%20Monitor%20Overview%20Gen.png).

This monitor allows [Home Manager](https://github.com/roscoe81/Home-Manager) to interwork with an EV charger over LoRaWAN via The Things Network. It can monitor the state of the EV charger, as well as performing lock outlet, unlock outlet and reset charger commands using the EV charger's Modbus RS485 interface (* See note about downlink command timing). The Things Network is used to support charger locations that aren't able to provide wifi coverage (e.g. in a basement garage). It requires customised TTN payload formats that can be found [here](https://github.com/roscoe81/ev-charger-monitor/tree/main/TTN%20Payload%20Formats) and the setup of a mosquitto bridge on the Home Manager side of the system.

* Note that the TTN functionality provides timely uplinking of charger state data, but downlink data (i.e. commands to the charger) are only sent after an uplink message. Therefore commands to the charger are not sent immediately and will be delayed. This does impact the functionality, but it's been minimised by varying the loop timings, based on the charger state.

## Hardware
![Hardware](https://github.com/roscoe81/ev-charger-monitor/blob/main/Photos/IMG_5237.jpg)
The [monitor](https://github.com/roscoe81/ev-charger-monitor/tree/main/Photos) uses a Pycom LoPy4, Pycom Expansion Board 3.0 and a Sparkfun BOB-10124 Transceiver Breakout for RS485 Modbus communications(P3 to RX-1, P4 to TX-0 and P8 to RTS)

**This project should only be constructed and deployed by a licenced electrician and its use might void charger and vehicle warranties. See LICENCE.md for disclaimers.**

## Operation
The system can sense the following charger states:

1. "Not Connected": The EV is not connected to the charger

2. "Connected and Locked": The EV is connected to the charger and the key switch on the charger has not been turned to start charging

3. "Charging": The charger is charging the EV battery

4. "Charged": The EV is charged to the required level. This state is normally triggered by the EV advising the charger.

The system has the following control functions (* See above note about command timing):

1. "Reset Charger": It's found that this can be used to commence EV charging when the charger is in the "Connected and Locked" state - even if the charger's key switch is still in the locked state.

2. "Lock Outlet": Places the charger in an error mode and interrupts the charging process. This shoukdn't be necessary because the EV will stop the charging process when the desired charge level is met.

3. "Unlock Outlet": Takes the charger out of error mode

ACKs are uplinked via TTN when each control command has been received.

## License
This project is licensed under the MIT License - see the LICENSE.md file for details

## Acknowledgements
The project has been developed by exploring some of the charger interworking functionality documented in https://github.com/cvvmedia/symcon.cvvmedia.ablchargepoint. The outcome, combined with my additional protocol analysis is [here](https://github.com/roscoe81/ev-charger-monitor/blob/main/Documentation/Charger%20Protocol.pdf).



