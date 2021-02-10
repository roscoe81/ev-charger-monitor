# ev-charger-monitor
Remotely monitors and controls a Mercedes-Benz Wallbox Home EV Charger via The Things Network(TTN) LoRaWAN.

## System Overview
![System Overview](https://github.com/roscoe81/ev-charger-monitor/blob/main/Documentation/Northcliff%20EV%20Charger%20Monitor%20Overview.png).

This monitor allows [Home Manager](https://github.com/roscoe81/Home-Manager) to interwork with an EV charger over LoRaWAN via The Things Network. It can monitor the state of the EV charger, as well as performing lock outlet, unlock outlet and reset charger commands. The Things Network is used to support locations that aren't able to provide wifi coverage (e.g. in a basement garage). It requires customised TTN payload formats that can be found [here](https://github.com/roscoe81/ev-charger-monitor/tree/main/TTN%20Payload%20Formats) and the setup of a mosquitto bridge on the Home Manager side of the system.

**Be aware that this project should only be constructed and deployed by a licenced electrician and its use might void charger and vehicle warranties. See LICENCE.md for disclaimers.**

## License
This project is licensed under the MIT License - see the LICENSE.md file for details



