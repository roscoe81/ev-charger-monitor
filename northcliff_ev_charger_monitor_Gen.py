from machine import UART
from machine import Pin
import time
from network import LoRa
import socket
import ubinascii
import pycom

def setup_ttn_region(ttn_region):
    lora = LoRa(mode=LoRa.LORAWAN, region=ttn_region)
    # Remove unused channels
    # leave channels 8-15 and 65
    for index in range(0, 8):
        lora.remove_channel(index)  # remove 0-7
    for index in range(16, 65):
        lora.remove_channel(index)  # remove 16-64
    for index in range(66, 72):
        lora.remove_channel(index)   # remove 66-71
    return lora

def join_ttn(ttn_app_eui, ttn_app_key, ttn_dev_eui, lora):
    print("Joining The Things Network")
    # create OTAA authentication parameters
    app_eui = ubinascii.unhexlify(ttn_app_eui)
    app_key = ubinascii.unhexlify(ttn_app_key)
    dev_eui = ubinascii.unhexlify(ttn_dev_eui)
    # join a network using OTAA (Over the Air Activation)
    lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0)
    # wait until the module has joined the network
    while not lora.has_joined():
        time.sleep(2.5)
        print('Not yet joined...')
    print('Joined')
    pycom.rgbled(0x001000) #Set LED to Green
    time.sleep(5)

def capture_charger_message():
    #print("Waiting for Charger Message")
    #pycom.rgbled(0x101010) # Set LED to white while waiting for message
    read_char = None
    while read_char != b">": # Look for response header
        read_char = uart.read(1)
    #print("Response Received. Capturing Data", read_char)
    response = read_char # Start response with header
    message_complete = False
    while message_complete == False: # Capture remaining message
        read_char = uart.read(1)
        if read_char == b"\r": # Look for CR
            #print("Found CR")
            pass
        elif read_char == b"\n": # Look for LF
            #print("Found LF")
            if response[-1:] == b"\r": # Message complete & valid when CR/LF
                #print("Found CR/LF")
                message_complete = True
                message_valid = True
        elif (read_char == b">" or read_char == b":"):
            # Abort message if another header is received before CR/LF
            message_complete = True
            message_valid = False
        response = response + read_char # Add character to reponse
        #print("Response", response)
    return response, message_valid

def update_device_id(device_id, message_format):
    #print("Old Message Types", message_format)
    for message in message_format:
        message_format[message] = message_format[message][0:1]+device_id+message_format[message][3:]
    #print("New Message Types", message_format)
    return message_format

def update_crc(message_format):
    for message in message_format:
        #print("With Old CRC", message_format[message])
        message_content = message_format[message][1:-4] # Remove header, CRC, CR and LF
        #print("Message Content", message_content)
        current_crc = message_format[message][-4:-2]
        #print("Current CRC", current_crc)
        valid_crc, required_crc = check_crc(message_content, current_crc)
        #print("Required CRC", required_crc)
        message_format[message] = message_format[message][0:1]+message_content+required_crc[2:].upper()+message_format[message][-2:]
        #print("With New CRC", message_format[message])
    return message_format

def process_charger_message(message, message_types):
    #print("Incoming Message", message)
    found_message_type = None # Reset message type
    message_content = message[1:-4] # Remove >, CRC, CR and LF
    #print("Message Content", message_content)
    crc = message[-4:-2]
    #print("CRC", crc)
    valid_crc, required_crc = check_crc(message_content, crc)
    if valid_crc:
        #print("CRC is Valid")
        # Check message type
        for mt in message_types:
            #print(mt, message_types[mt], message[0:len(message_types[mt])])
            if message_types[mt] == message[0:len(message_types[mt])]:
                found_message_type = mt
        if found_message_type != None: # Ignore unrecognised messages
            #print("Found Message Type", found_message_type, message_types[found_message_type])
            return found_message_type
    else: # found_message_type is None if crc is invalid
        print("Invalid CRC")
        return found_message_type

def check_crc(message_content, in_crc):
    #print("Checking CRC")
    #print("Raw CRC", in_crc)
    b = [message_content[i:i+2] for i in range(0, len(message_content), 2)] # Build a list of each non-checksum Packet 2 byte in hex string form
    #print("B", b)
    c = [int(i, 16) for i in b] # Convert the hex string from list into a list of integers
    #print("C", c)
    d = hex(((sum(c) ^ 0xff) + 1) & 0xff) # Sum the integer list
    #print("D", d)
    #print ("Valid CRC is", d)
    #print ("Actual CRC", hex(int(in_crc,16)))
    if d == hex(int(in_crc, 16)):
        #print("Same")
        return True, d
    else:
        #print("Different")
        return False, d

def determine_panel_display_state(message, header):
    header_length = len(header)
    charger_state = b"00"
    charger_state = message[(header_length): (header_length + 2)]
    if charger_state == b'A1': # Not Connected. Blue
        pycom.rgbled(0x000010)
        charger_state_text = "Not Connected"
    elif charger_state == b'B1': # Connected & Locked with the Key Switch. Yellow
        pycom.rgbled(0x101000)
        charger_state_text = "Connected and Locked"
    elif charger_state == b'C2': # Charging. Green
        pycom.rgbled(0x001000)
        charger_state_text = "Charging"
    elif charger_state == b'B2': # Charged. White
        pycom.rgbled(0x101010)
        charger_state_text = "Charged"
    elif charger_state == b'E0': # E2 Mode. Purple
        pycom.rgbled(0x100010)
        charger_state_text = "Outlet Locked"
    elif charger_state == b'E2': # E2 Mode. Purple
        pycom.rgbled(0x100010)
        charger_state_text = "E2"
    else:
        pycom.rgbled(0x100000) # Unknown. Red
        charger_state_text = "Unknown"
    return charger_state, charger_state_text

def uplink_panel_display(charger_state, charger_state_text, s):
    s.setblocking(True)
    # send data
    print('Sending "' + charger_state_text + '" Message to TTN: ' + str(hex(int(charger_state, 16))))
    s.send(ubinascii.unhexlify(charger_state))
    # make the socket non-blocking
    # (because if there's no data received it will block forever...)
    s.setblocking(False)

def process_received_data(data, device_id):
    if data == b'\x01':
        print("Received Lock Outlet Command")
        lock_outlet(device_id)
        ack_msg = b'AA'
    elif data == b'\x02':
        print("Received Unlock Outlet Command")
        unlock_outlet(device_id)
        ack_msg = b'BB'
    elif data == b'\x03':
        print("Received Reset Charger Command")
        reset_charger(device_id)
        ack_msg = b'CC'
    else:
        print("Received Unknown Command:", data)
        ack_msg = b'DD'
    return ack_msg

def lock_outlet(device_id): # Disable the charger by putting it into E0 Mode
    message = ":" + device_id.decode("utf-8") + "100005000102E0E027\r\n"
    uart.write(message)
    time.sleep(0.02)
    uart.write(message)
    time.sleep(0.02)

def unlock_outlet(device_id): # Enable the charger after being locked by "Lock Outlet"
    message = ":" + device_id.decode("utf-8") + "100005000102A1A1A5\r\n"
    uart.write(message)
    time.sleep(0.02)
    uart.write(message)
    time.sleep(0.02)

def reset_charger(device_id): # Resets Charger and starts charging if it's in "Connected Locked" mode
    message = ":" + device_id.decode("utf-8") + "1000050001025A5A33\r\n"
    uart.write(message)
    time.sleep(0.02)
    uart.write(message)
    time.sleep(0.02)

def send_ack_to_ttn(ack_msg):
    s.setblocking(True)
    # send data
    #print("Sending Data", hex(int(charger_state, 16)))
    #s.send(ubinascii.unhexlify(charger_state))
    print("Sending Ack")
    s.send(ubinascii.unhexlify(ack_msg))
    # make the socket non-blocking
    # (because if there's no data received it will block forever...)
    s.setblocking(False)

def send_control_command(arg): # Used to test handling of received commands
    global next_command
    comms_led.value(0)
    uart_flow.value(1) # Set UART to transmit
    if next_command == 0:
        print("Reset Charger")
        reset_charger(b'01')
        next_command += 1
    elif next_command == 1:
        print("Locking Outlet")
        lock_outlet(b'01')
        next_command += 1
    elif next_command == 2:
        print("Unlocking Outlet")
        unlock_outlet(b'01')
        next_command = 0
    else:
        pass
    uart_flow.value(0) # Set UART to receive
    comms_led.value(1)

print("Northcliff EV Charger Monitor Gen V1.5")
# Set up TTN Access
ttn_app_eui = '<Your TTN App EUI>'
ttn_app_key = '<Your TTN App Key>'
ttn_dev_eui = '<Your TTN Device EUI>'

# Set up Charger reporting message types
message_types = {"Panel Display": b">01030204", "Serial Number":
b">01031050", "Status": b">01030A2E", "Scan Response":
b">010304"}

received_data = None
previous_processed_message = None
heartbeat_counter = 0
new_message_counter = 0
next_command = 0
charger_state = b'A1' # Set starting state to "Not Connected"
use_S1_to_test_commands = False # Set to true to use S1 to cycle through commands

# disable LED heartbeat (so we can control the LED)
pycom.heartbeat(False)
# set LED to red while attempting to join LoraWAN
pycom.rgbled(0x100000)
lora = setup_ttn_region(LoRa.AU915)
join_ttn(ttn_app_eui, ttn_app_key, ttn_dev_eui, lora)
# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
# set the LoRaWAN data rate
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
# Set EV Charger Modbus Comms
s.settimeout(3.0) # configure a timeout value of 3 seconds
uart = UART(1, baudrate=38400, bits=8, parity=UART.EVEN, stop=1)
uart_flow = Pin('P8', mode=Pin.OUT) # Set up UART flow control. 0=receive, 1=send
uart_flow.value(0) # Set UART to receive
comms_led = Pin('P9', mode=Pin.OUT) # Set up Comms LED. 0=On, 1=Off
comms_led.value(1) # Set Comms LED to Off

if use_S1_to_test_commands:
    button = Pin('P10', mode=Pin.IN, pull=Pin.PULL_UP) #Set up S1 to cycle through command tests
    button.callback(Pin.IRQ_RISING, handler=send_control_command)
else:
    print("S1 Disabled")

# Find Charger Device ID
print("Finding Charger Device ID")
comms_led.value(0)
response, message_valid = capture_charger_message()
comms_led.value(1)
if message_valid:
    device_id = response[1:3]
    print("Charger Device ID:", device_id)
    message_types = update_device_id(device_id, message_types) # Update message types with correct Device ID
    print("Waiting for Stable Charger Message")
    while True:
        comms_led.value(1)
        response, message_valid = capture_charger_message()
        comms_led.value(0)
        if message_valid:
            found_message_type = process_charger_message(response, message_types)
            if found_message_type == "Panel Display":
                charger_state, charger_state_text = determine_panel_display_state(response, message_types["Panel Display"])
                #print(response, charger_state, "Heartbeat Counter:", heartbeat_counter, "New Message Counter:", new_message_counter)
                if response != previous_processed_message:
                    if new_message_counter >= 20 and charger_state != b'A1' or new_message_counter >= 4 and charger_state == b'A1':
                        # Process new messages after ensuring that they're stable over 20 seconds
                        # (overcomes issues with the interim "Charging Completed" message commencing the charging process)
                        send_uplink = True
                    else:
                        send_uplink = False
                        new_message_counter +=1
                        if charger_state == b'A1':
                            remaining_cycles = 4 - new_message_counter
                        else:
                            remaining_cycles = 20 - new_message_counter
                        print("Cycles until Message Capture:", remaining_cycles)
                elif ((charger_state == b'B1' or charger_state == b'E0') and heartbeat_counter >= 280 or charger_state == b'A1' and heartbeat_counter >= 716 or
                 charger_state != b'A1' and charger_state != b'B1' and charger_state != b'E0' and heartbeat_counter >= 3580):
                    # Process old messages every 5 minutes if in "Connected and Locked" or "Outlet Locked" state and every hour in other states. That allows the ability to receive timely downlink TTN commands.
                    send_uplink = True
                else:
                    # Don't send uplinks in other cases
                    send_uplink = False
                    heartbeat_counter +=1
                    if charger_state == b'A1':
                        remaining_cycles = 716 - heartbeat_counter
                    elif charger_state == b'B1' or charger_state == b'E0':
                        remaining_cycles = 280 - heartbeat_counter
                    else:
                        remaining_cycles = 3580 - heartbeat_counter
                    print("Cycles until Charger Message Update:", remaining_cycles)
                if send_uplink:
                    #print("Found and processing", response, "Previous Message", previous_processed_message, "Charger State",
                    # charger_state, "Heartbeat Counter", heartbeat_counter, "New Message Counter", new_message_counter)
                    heartbeat_counter = 0
                    new_message_counter = 0
                    previous_processed_message = response
                    comms_led.value(0)
                    uplink_panel_display(charger_state, charger_state_text, s)
                    comms_led.value(1)
                    time.sleep(3) # Wait for data to be sent and received
                    try:
                        data = s.recv(64) # Capture any received downlink message
                    except socket.timeout:
                        print('No packet received')
                    if data != b'':
                        print('Received', data, 'message from TTN')
                        comms_led.value(0)
                        # send message after a panel message has been received
                        response, message_valid = capture_charger_message()
                        uart_flow.value(1) # Set UART to transmit
                        ack_msg = process_received_data(data, device_id)
                        if ack_msg != b"DD": # Only ack valid messages
                            uart_flow.value(0) # Set UART to receive
                            send_ack_to_ttn(ack_msg)
                            previous_processed_message = None
                        comms_led.value(1)
                    print("Waiting for Charger Message Update")
            elif found_message_type == "Serial Number": # Future capability
                print("Found Serial Number Message. Not Used.", response)
            elif found_message_type == "Status": # Future capability
                print("Found Status Message. Not Used.", response)
            elif found_message_type == "Scan Response": # Future capability
                print("Found Scan Response Message. Not Used.", response)
            else:
                print("Unrecognised Charger Message", response)
        else:
            print("Invalid Charger Message", response)
            pycom.rgbled(0x100010) # Set to Purple
else:
    print("Couldn't decode Device ID")
    pycom.rgbled(0x100010) # Set to Purple
