# EE250 Project

# All imports
import sys
import paho.mqtt.client as mqtt
import time
import grovepi as gp
#import threading # has Lock, a key. you cannot perform operations without the key

#lock = threading.Lock()

# From GrovePi Git repository
if sys.platform == 'uwp':
    import winrt_smbus as smbus
    bus = smbus.SMBus(1)
else:
    import smbus
    import RPi.GPIO as GPIO
    rev = GPIO.RPI_REVISION
    if rev == 2 or rev == 3:
        bus = smbus.SMBus(1)
    else:
        bus = smbus.SMBus(0)

# I2C addresses (from GrovePi Git repo)
DISPLAY_RGB_ADDR = 0x62
DISPLAY_TEXT_ADDR = 0x3e

# Set backlight (from GrovePi Git repo)
def setRGB(r,g,b):
    bus.write_byte_data(DISPLAY_RGB_ADDR,0,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,1,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,0x08,0xaa)
    bus.write_byte_data(DISPLAY_RGB_ADDR,4,r)
    bus.write_byte_data(DISPLAY_RGB_ADDR,3,g)
    bus.write_byte_data(DISPLAY_RGB_ADDR,2,b)

# Send command to display (from GrovePi Git repo)
def textCommand(cmd):
    bus.write_byte_data(DISPLAY_TEXT_ADDR,0x80,cmd)

# Set display text \n for second line (from GrovePi Git repo)
def setText(text):
    textCommand(0x01) # clear display
    time.sleep(.05)
    textCommand(0x08 | 0x04) # display on, no cursor
    textCommand(0x28) # 2 lines
    time.sleep(.05)
    count = 0
    row = 0
    for c in text:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            textCommand(0xc0)
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR,0x40,ord(c))

# Update the display without erasing the display (from GrovePi Git repo)
def setText_norefresh(text):
    textCommand(0x02) # return home
    time.sleep(.05)
    textCommand(0x08 | 0x04) # display on, no cursor
    textCommand(0x28) # 2 lines
    time.sleep(.05)
    count = 0
    row = 0
    while len(text) < 32: #clears the rest of the screen
        text += ' '
    for c in text:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            textCommand(0xc0)
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR,0x40,ord(c))

# Executed when client receives connection acknowledgement packet response from server
def on_connect(client, userdata, flags, rc):
    print("Connected to server (i.e., broker) with result code "+str(rc))

    # Subscribe to laptop data topic
    client.subscribe("zhujessi/laptop")
    # Add custom callback
    client.message_callback_add("zhujessi/laptop", on_message_from_laptop)

# Default callback for messages received when another node publishes message client is subscribed to
def on_message(client, userdata, msg):
    print("Default callback - topic: " + msg.topic + "   msg: " + str(msg.payload, "utf-8"))

# laptop weather data callback 
def on_message_from_laptop(client, userdata, message):
    #with lock:
    print("Custom callback - Laptop")

    blinds_msg = str(message.payload, "utf-8")
    print("Blinds message: " + blinds_msg)
    
    # Print open/close blinds message on LCD
    setText_norefresh(blinds_msg)
    if blinds_msg == "Close blinds":
        setRGB(20, 228, 255) # Set background color of LCD to blue for close blinds
    elif blinds_msg == "Open blinds":
        setRGB(20, 245, 90) # Set background color of LCD to green for open blinds
    else:
        print("Error: unrecognized blinds message")


if __name__ == '__main__':
	# Create client object
    client = mqtt.Client()
    # Attach default callback defined above for incoming mqtt messages
    client.on_message = on_message
    # Attach the on_connect() callback function defined above to mqtt client
    client.on_connect = on_connect
    # Connect to public broker since Eclipse is down
    client.connect(host="test.mosquitto.org", port=1883)
    # Spawn a separate thread to handle incoming and outgoing mqtt messages
    client.loop_start()
    
    while True:
    	# Connect light sensor to analog port A0 of GrovePi
    	light_sensor = 0

        #try:
            #with lock:
            while True:
                # Read sensor value from light sensor
                sensor_value = gp.analogRead(light_sensor)
                client.publish("zhujessi/light", sensor_value)
                print("Publishing light sensor value")

            	time.sleep(1)		# Prevent i2c overload
            
        #except IOError:
            #print("Error")
