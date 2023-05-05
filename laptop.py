# EE250 Project


# All imports
import paho.mqtt.client as mqtt
import requests
import json
import time
import weather
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Variables
WEATHER_API_KEY = '308ed26fa6a144f8961195323230405'  	# API key for Weather API
current_light_value = 10 								# Arbitrary

# Topics
laptop_path = "zhujessi/laptop"		# laptop data topic
light_path = "zhujessi/light" 		# light sensor topic

# Executed when client receives connection acknowledgement packet response from server
def on_connect(client, userdata, flags, rc):
    print("Connected to server (i.e., broker) with result code "+str(rc))

    # subscribe to the light sensor topic
    client.subscribe(light_path, qos=1)
    client.message_callback_add(light_path, on_message_from_light)

# Default callback for messages received when another node publishes message client is subscribed to
def on_message(client, userdata, msg):
    print("Default callback - topic: " + msg.topic + "   msg: " + str(msg.payload, "utf-8"))

# Custom message callback
def on_message_from_light(client, userdata, message):
    # Laptop received light sensor data from rpi
    # Rpi published light sensor value to subscribed topic
    print("Custom callback - Light")
    print("Light sensor reading: " + str(message.payload, "utf-8"))

    # Update global light sensor value variable
    global current_light_value
    current_light_value = int(str(message.payload, "utf-8"))
    print("Current light value in callback: " , current_light_value)

# Obtain relevant weather info from API
def extract_weather_info(zipcode):
    params = {
        'key': WEATHER_API_KEY,
        'q': zipcode,
        'days': 5,
    }

    # Make get request to API
    response_current = requests.get('http://api.weatherapi.com/v1/current.json', params)
    response_forecast = requests.get('http://api.weatherapi.com/v1/forecast.json', params)

    if response_current.status_code == 200 and response_forecast.status_code == 200:
        cloud_data = response_current.json()
        visibility_data = response_forecast.json()

        # Extract the cloud cover percentage, visibility and integer representing whether it is day or not from the JSON response
        clouds = cloud_data['current']['cloud']
        day_or_night = cloud_data['current']['is_day']
        visibility = visibility_data['current']['vis_km']
        print(clouds)
        print(day_or_night)
        print(visibility)

        return clouds, day_or_night, visibility

    else:
        print('Error: API response code %d' % response.status_code)
        print(response.text)
        return 0.0, 0.0, 0.0

# Function to compare weather API light info with light sensor value to decide if blinds
# should be open or closed.
def compare_light(light_sensor_value, weather_api_light, weather_api_day):
    
    blinds_msg = ""
    
    if weather_api_day == 0:								# Close blinds at night
    	blinds_msg = "Close blinds"
    elif weather_api_day == 1:								# Only open blinds during day
        if weather_api_light < light_sensor_value:			# Inside is brighter
            blinds_msg = "Close blinds"
        elif weather_api_light > light_sensor_value:	
            blinds_msg = "Open blinds"						# Outside is brighter
    
    return blinds_msg

# Function to weight different pieces of info from weather API and assign 1 light value as
# a percentage
def gen_outside_light_value(weather_api_cloud, weather_api_visibility):
    # Weights
    CLOUD_WEIGHT = 85 
    VISIBILITY_WEIGHT = 15

    # Convert visibility in km to percentage
    visibility_percent = weather_api_visibility / 296	# 296 km is max visibility on clear day

    # Return outside light value (higher value = brighter)
    outside_light = ((CLOUD_WEIGHT*(100-weather_api_cloud)) + (VIS_WEIGHT*visibility_percent))/100
    
    return outside_light

# Function to take light sensor reading and assign 1 light value as a percentage
def sensor_signal_processing(sensor_light):

    # return inside light value out of 100 --> higher value = lighter
    inside_light = (sensor_light / 800)*100				# 800 is max sensor light value
    
    return inside_light


# Function pulls weather data, updates plot of light sensor values and called every 2 secs
def update_plot(i, xdata, ydata):

    xdata.append(dt.datetime.now().strftime('%H:%M:%S.%f'))
    ydata.append(current_light_value)
    print(current_light_value)

    # Show most recent 10 data points
    xdata = xs[-10:]
    ydata = ys[-10:]

    # draw x and y lists, plotting the points according to list contents
    ax.clear()
    ax.plot(xdata, ydata, marker = 'o', color = 'darkblue', alpha = 0.5)

    # formatting plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('Light Sensor Readings over Time')
    plt.ylabel('Light Value')


    # getting current weather data by calling weather initialization function from weather.py
    zipcode = 90089 									# My current LA zip code
    curr_clouds, day_or_night, curr_vis = extract_weather_info(zipcode)
    
    print("Clouds: " + str(curr_clouds))
    print("Visibility: " + str(curr_vis))
    print("Day? " + str(day_or_night))

    # calculating single value for outside light out of 100
    outside_lightval = gen_outside_light_value(curr_clouds, curr_vis)
    print("Outside percentage:", outside_lightval)

    # calculating single value for inside light out of 100
    inside_lightval = sensor_signal_processing(current_light_value)
    print("Inside percentage:", inside_lightval)

    # publishing the result (open vs. closed blinds) to the pi
    result = compare_light(inside_lightval, outside_lightval, day_or_night)
    client.publish(laptop_path, str(result))
    print("Message should be: " + str(result))

    
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

    # Create empty figure
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    xdata, ydata = [], []

    # Update figure every 2 sec
    ani = FuncAnimation(fig, update_plot, fargs=(xdata, ydata), interval=2000)
    plt.show()
        
