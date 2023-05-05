# EE250 Project

# All imports
import paho.mqtt.client as mqtt
import requests
import json
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Variables
WEATHER_API_KEY = "9ee3f95e9c35480b80a55136230505"  	# API key for Weather API
current_light_value = 10 				# Arbitrary initial value for global variable

# Executed when client receives connection acknowledgement packet response from server
def on_connect(client, userdata, flags, rc):
    print("Connected to server (i.e., broker) with result code "+str(rc))

    # Subscribe to light sensor topic
    client.subscribe("zhujessi/light", qos=1)
    # Add custom callback
    client.message_callback_add("zhujessi/light", on_message_from_light)

# Default callback for messages received when another node publishes message client is subscribed to
def on_message(client, userdata, msg):
    print("Default callback - topic: " + msg.topic + "   msg: " + str(msg.payload, "utf-8"))

# Custom message callback
def on_message_from_light(client, userdata, message):
    print("Custom callback - Light")
    
    # Print sensor value
    sensor_reading = str(message.payload, "utf-8")
    print("Light sensor reading: " + sensor_reading)

    # Update global light sensor value variable
    global current_light_value
    current_light_value = int(sensor_reading)

# Obtain relevant weather info from API
def extract_weather_info(zipcode):
    params = {
        "key": WEATHER_API_KEY,
        "q": zipcode,
        "days": 5,
    }

    # Make get request to API
    response_current = requests.get("http://api.weatherapi.com/v1/current.json", params)
    response_forecast = requests.get("http://api.weatherapi.com/v1/forecast.json", params)

    if response_current.status_code == 200 and response_forecast.status_code == 200:
        cloud_data = response_current.json()
        visibility_data = response_forecast.json()

        # Extract the cloud cover, visibility, and whether day or night
        clouds = cloud_data['current']['cloud']
        day_or_night = cloud_data['current']['is_day']
        visibility = visibility_data['current']['vis_km']

        return clouds, day_or_night, visibility

    else:
        print("Error: API response code %d" % response.status_code)
        print(response.text)
        return 0.0, 0.0, 0.0

# Function to compare weather API light info with light sensor value to decide if blinds
# should be open or closed.
def compare_light(weather_api_day_or_night, light_sensor_value, weather_api_light):
    
    blinds_msg = ""
    
    if weather_api_day_or_night == 0:						# Close blinds at night
    	blinds_msg = "Close blinds"
    elif weather_api_day_or_night == 1:						# Only open blinds during day
        if weather_api_light < light_sensor_value:				# Inside is brighter
            blinds_msg = "Close blinds"
        elif weather_api_light >= light_sensor_value:	
            blinds_msg = "Open blinds"						# Outside is brighter
    else:
        print("Error: Unrecognized if day or night")
    
    return blinds_msg

# Function to calculate light percentage inside (based on sensor) and outside (based on API)
def data_processing(sensor_light, weather_api_cloud, weather_api_visibility):
    
    # Return inside light value as percentage (higher value = brighter)
    inside_light = (sensor_light / 800)*100				# 800 is max sensor light value

    # Convert visibility in km to percentage
    visibility_percent = weather_api_visibility / 296	# 296 km is max visibility on clear day

    # Return outside light value as percentage (higher value = brighter) using weights
    # (cloud coverage much more important than visibility)
    outside_light = ((85*(100-weather_api_cloud)) + (15*visibility_percent))/100
    
    return inside_light, outside_light

# Function to control blinds by publishing correct blinds message
def control_blinds(zipcode):

    # Get weather info at location
    api_clouds, day_or_night, api_visibility = extract_weather_info(zipcode)
    
    print("Clouds: " + str(api_clouds))
    print("Visibility: " + str(api_visibility))
    if day_or_night == 0:
    	print("Night")
    elif day_or_night == 1:
    	print("Day")
    else:
    	print("Error: Unrecognized if day or night")

    # Calculate inside and outside light percentages
    inside_light, outside_light = data_processing(current_light_value, api_clouds, api_visibility)
    print("Inside percentage:", inside_light)
    print("Outside percentage:", outside_light)

    # Publish open/close blinds message
    blinds_msg = compare_light(day_or_night, inside_light, outside_light)
    client.publish("zhujessi/laptop", str(blinds_msg))

# Function updates plot and blinds message every 2 secs
def update_plot(i, x, y):

    # Add newest time and sensor reading
    x.append(datetime.now().strftime("%H:%M:%S"))
    y.append(current_light_value)

    # Show most recent 10 data points
    x = x[-10:]
    y = y[-10:]

    # Plot
    ax.clear()
    ax.plot(x, y, '.-b', linewidth=1, markersize=10)

    # Format plot
    ax.set_xticks(x)
    ax.set_xticklabels(x, rotation=45)
    plt.subplots_adjust(bottom=0.2)
    plt.title("Most Recent Light Sensor Readings")
    plt.ylabel("Light Reading")
    plt.xlabel("Time")

    # Find and publish correct blinds message at given location
    current_zipcode = 90089 								# My current LA zip code
    control_blinds(current_zipcode)

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
    x, y = [], []

    # Update figure every 2 sec
    ani = FuncAnimation(fig, update_plot, fargs=(x, y), interval=2000)
    plt.show()
