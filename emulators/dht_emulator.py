import sys
import random
import json
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout,
                            QFormLayout, QLineEdit, QLabel, QPushButton, QSpinBox)
from PyQt5.QtCore import QTimer, Qt
import paho.mqtt.client as mqtt

# Update import path to access mqtt_config from parent directory
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mqtt_config import (BROKER_IP, BROKER_PORT, USERNAME, PASSWORD,
                        TEMP_TOPIC, HUMIDITY_TOPIC, CLIENT_ID_PREFIX)

class DHTEmulator(QMainWindow):
    """Temperature and Humidity Sensor Emulator"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DHT Sensor Emulator")
        self.setGeometry(100, 100, 400, 300)

        # Initialize MQTT Client
        self.client_id = f"{CLIENT_ID_PREFIX}dht_{random.randint(0, 1000)}"
        self.mqtt_client = mqtt.Client(client_id=self.client_id)
        
        # Define MQTT callbacks
        def on_message(client, userdata, message):
            print(f"Received message on topic {message.topic}: {message.payload.decode()}")
        
        self.on_message = on_message
        
        self.mqtt_client.username_pw_set(USERNAME, PASSWORD)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.connected = False

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Create form layout for inputs
        form_layout = QFormLayout()
        
        # Temperature input
        self.temp_input = QLineEdit()
        self.temp_input.setPlaceholderText("24.0")
        self.temp_input.setText("24.0")
        self.temp_input.setAlignment(Qt.AlignRight)
        form_layout.addRow("Temperature (°C):", self.temp_input)

        # Humidity input
        self.humidity_input = QLineEdit()
        self.humidity_input.setPlaceholderText("50.0")
        self.humidity_input.setText("50.0")
        self.humidity_input.setAlignment(Qt.AlignRight)
        form_layout.addRow("Humidity (%):", self.humidity_input)

        # Update interval input
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 60)
        self.interval_input.setValue(5)
        self.interval_input.setSuffix(" seconds")
        form_layout.addRow("Update Interval:", self.interval_input)

        # Status label
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red;")
        form_layout.addRow("Status:", self.status_label)

        layout.addLayout(form_layout)

        # Add buttons
        self.send_button = QPushButton("Send Now")
        self.send_button.clicked.connect(self.manual_send)
        self.send_button.setEnabled(False)
        self.send_button.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white;")
        layout.addWidget(self.send_button)

        # Timer for automatic updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_send)
        
        # Connect to broker
        try:
            self.status_label.setText("Connecting to broker...")
            self.mqtt_client.connect(BROKER_IP, BROKER_PORT)
            self.mqtt_client.loop_start()
        except Exception as e:
            self.status_label.setText(f"Connection Error: {str(e)}")
            print(f"Connection Error: {str(e)}")

        # Start timer
        self.timer.start(5000)  # Start with 5 second interval
        self.interval_input.valueChanged.connect(self.update_timer_interval)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.status_label.setText("Connected to broker")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.send_button.setEnabled(True)
            print("DHT Emulator connected to broker")
        else:
            self.status_label.setText(f"Connection failed with code {rc}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.send_button.setEnabled(False)

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        self.status_label.setText("Disconnected from broker")
        self.status_label.setStyleSheet("color: red;")
        self.send_button.setEnabled(False)
        print("DHT Emulator disconnected from broker")

    def update_timer_interval(self, value):
        self.timer.setInterval(value * 1000)

    def get_sensor_data(self):
        try:
            temp = float(self.temp_input.text() or 24.0)
            humidity = float(self.humidity_input.text() or 50.0)
        except ValueError:
            temp = 24.0 + random.uniform(-2, 2)
            humidity = 50.0 + random.uniform(-5, 5)
        
        return round(temp, 1), round(humidity, 1)

    def publish_data(self, temp, humidity):
        if not self.connected:
            self.status_label.setText("Not connected to broker")
            return

        # Get current timestamp
        timestamp = datetime.now().isoformat()

        # Publish temperature
        temp_payload = json.dumps({
            "value": temp,
            "unit": "celsius",
            "sensor_id": self.client_id,
            "timestamp": timestamp
        })
        print(f"Publishing temperature: {temp}°C")
        self.mqtt_client.publish(TEMP_TOPIC, temp_payload, qos=1)

        # Publish humidity
        humidity_payload = json.dumps({
            "value": humidity,
            "unit": "percent",
            "sensor_id": self.client_id,
            "timestamp": timestamp
        })
        print(f"Publishing humidity: {humidity}%")
        self.mqtt_client.publish(HUMIDITY_TOPIC, humidity_payload, qos=1)

        self.status_label.setText(f"Published: {temp}°C, {humidity}%")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")

    def manual_send(self):
        temp, humidity = self.get_sensor_data()
        self.publish_data(temp, humidity)

    def auto_send(self):
        # Get current values or generate random ones
        try:
            current_temp = float(self.temp_input.text() or 24.0)
            current_humidity = float(self.humidity_input.text() or 50.0)
        except ValueError:
            current_temp = 24.0
            current_humidity = 50.0

        # Add small random variations
        temp = round(current_temp + random.uniform(-0.5, 0.5), 1)
        humidity = round(current_humidity + random.uniform(-2, 2), 1)

        # Update display
        self.temp_input.setText(str(temp))
        self.humidity_input.setText(str(humidity))

        # Publish
        self.publish_data(temp, humidity)

    def closeEvent(self, event):
        print("Shutting down DHT Emulator")
        self.timer.stop()
        self.mqtt_client.loop_stop()
        if self.connected:
            self.mqtt_client.disconnect()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DHTEmulator()
    window.show()
    sys.exit(app.exec_())
