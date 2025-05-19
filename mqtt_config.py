# MQTT configuration
"""
Simple MQTT configuration for Smart AC Control System
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Broker configuration - Using HiveMQ public broker
BROKER_IP = 'broker.hivemq.com'
BROKER_PORT = 1883
USERNAME = ''  # No authentication needed for public broker
PASSWORD = ''

# Topic configuration
BASE_TOPIC = "smart_ac"

# Device topics
TEMP_TOPIC = f"{BASE_TOPIC}/temperature"  # Temperature readings from DHT
HUMIDITY_TOPIC = f"{BASE_TOPIC}/humidity"  # Humidity readings from DHT
SETPOINT_TOPIC = f"{BASE_TOPIC}/setpoint"  # Temperature setpoint from knob
CONTROL_TOPIC = f"{BASE_TOPIC}/control"    # Control commands to relay
STATUS_TOPIC = f"{BASE_TOPIC}/status"      # Relay status updates
ALARM_TOPIC = f"{BASE_TOPIC}/alarm"        # System alarms

# QoS levels
DEFAULT_QOS = 1  # At least once delivery

# Other MQTT settings
CLIENT_ID_PREFIX = "smart_ac_"
KEEP_ALIVE = 60  # seconds

# Define MQTT topics
temp_topic_static = "home/temperature"  # Topic for temperature readings
status_topic_static = "home/status"  # Topic for device status updates
alarm_topic_static = "home/alarm"  # Topic for alarm notifications
temp_topic = "pr/home/dht_456_YY/temp"  # Define the topic for temperature

import socket

nb=1 # 0- HIT-"139.162.222.115", 1 - open HiveMQ - broker.hivemq.com
brokers=[str(socket.gethostbyname('vmm1.saaintertrade.com')), str(socket.gethostbyname('broker.hivemq.com'))]
ports = ['80','1883'] # should be modified for HIT
usernames = ['MATZI',''] # should be modified for HIT
passwords = ['MATZI',''] # should be modified for HIT
broker_ip=brokers[nb]
port=ports[nb]
username = usernames[nb]
password = passwords[nb]
conn_time = 0 # 0 stands for endless
mzs=['matzi/','']
sub_topics =[mzs[nb]+'#','#']
pub_topics = [mzs[nb]+'test','test']

broker_ip=brokers[nb]
broker_port=ports[nb]
username = usernames[nb]
password = passwords[nb]
sub_topic_dynamic = sub_topics[nb]
pub_topic_dynamic = pub_topics[nb]
pub_topic = pub_topics[nb]
