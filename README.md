## EE 250 Project

### Team Members:
- Jessica Zhu
- No second team member

### Github Repo: 
https://github.com/jessicazhu318/project.git

### Demo video: 
[insert link]

### Sources:
- Received help with idea generation from Ariana Goldstein (former EE250 student)
- GrovePi LCD with RGB: https://github.com/DexterInd/GrovePi/blob/master/Software/Python/grove_rgb_lcd/grove_rgb_lcd.py
- Weather API: https://www.weatherapi.com/
- MQTT Broker: https://test.mosquitto.org/

### List of libraries:
The following external libraries were used:
- paho mqtt
- requests
- matplotlib
- grovepi

### Instructions:
To run the system, first install all external libraries listed above. 
On the laptop, use the following commands to install the necessary libraries:
- pip install paho-mqtt
- pip install requests
- pip install matplotlib
<br>
On the RaspberryPi (RPi), use the following commands to install the necessary libraries:
- pip install paho-mqtt
- pip install grovepi

Once all libraries have been installed, clone the Github repository listed above on BOTH
the laptop and RPi using the git clone command. Once cloned, run the laptop.py file in the
terminal of the laptop using the python3 command, and run the rpi.py file in the terminal 
of the RPi also using the python3 command.

Now that the system is running, a figure should pop up on the laptop showing the plot of
most recent light sensor readings. Additionally, information should be printing in the
terminal of the laptop, including cloud coverage, visibility, whether it is day or night 
time, brightness percentages both inside and outside, and the light sensor reading.
