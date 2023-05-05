# EE250 Project


# All imports
import paho.mqtt.client as mqtt
import time
import grovepi as gp
import threading # has Lock, a key. you cannot perform operations without the key

lock = threading.Lock()

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

# I2C addresses
DISPLAY_RGB_ADDR = 0x62
DISPLAY_TEXT_ADDR = 0x3e

# Set backlight to (R,G,B) (values from 0..255 for each)
def setRGB(r,g,b):
    bus.write_byte_data(DISPLAY_RGB_ADDR,0,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,1,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,0x08,0xaa)
    bus.write_byte_data(DISPLAY_RGB_ADDR,4,r)
    bus.write_byte_data(DISPLAY_RGB_ADDR,3,g)
    bus.write_byte_data(DISPLAY_RGB_ADDR,2,b)

# Send command to display (no need for external use)
def textCommand(cmd):
    bus.write_byte_data(DISPLAY_TEXT_ADDR,0x80,cmd)

# Set display text \n for second line (or auto wrap)
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

# Update the display without erasing the display
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

# Topics
laptop_path = "zhujessi/laptop"		# laptop data topic
light_path = "zhujessi/light" 		# light sensor topic

# on_connect function to indicate whether we have connected to the broker successfully or not
def on_connect(client, userdata, flags, rc):
    print("Connected to server (i.e., broker) with result code "+str(rc))

    # subscribing to laptop data topic
    client.subscribe(laptop_path)
    client.message_callback_add(laptop_path, on_message_from_laptop)

# default message callback
def on_message(client, userdata, msg):
    print("on_message: " + msg.topic + " " + str(msg.payload, "utf-8"))

# laptop weather data callback 
def on_message_from_laptop(client, userdata, message):
    with lock:
        print("In data callback")

        # sets the text on the LCD to open blinds or close blinds
        setText_norefresh(str(message.payload, "utf-8"))
        if str(message.payload, "utf-8") == "Open blinds":
            # to indicate that we should open the blinds, set background color to yellow
            setRGB(247, 255, 20)
        else:
            # to indicate that we should close the blinds, set background color to blue
            setRGB(20, 228, 255)


if __name__ == '__main__':
    client = mqtt.Client()
    client.on_message = on_message
    client.on_connect = on_connect
    client.connect(host="test.mosquitto.org", port=1883)
    client.loop_start()

    # setting up connections on the Grovepi
    light_sensor = 0 # light sensor should be plugged into A0
    # pinMode(light_sensor,"INPUT")
    # lcd should be plugged into an I2C port. no code necessary to declare this, just wiring
    
    while True:
        try:
            with lock:
                # monitoring and publishing light sensor
                sensor_value = gp.analogRead(light_sensor)
                client.publish(light_path, sensor_value)

            time.sleep(1)
            
        except IOError:
            print("Error")
