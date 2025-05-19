import sys
import random
import json
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout,
                            QLabel, QPushButton, QDial)
from PyQt5.QtCore import Qt
import paho.mqtt.client as mqtt

# Update import path to access mqtt_config from parent directory
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mqtt_config import (BROKER_IP, BROKER_PORT, USERNAME, PASSWORD,
                        SETPOINT_TOPIC, CLIENT_ID_PREFIX)

class KnobEmulator(QMainWindow):
    """Temperature Setpoint Knob Emulator"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Temperature Setpoint Knob")
        self.setGeometry(100, 100, 400, 300)

        # Initialize MQTT Client
        self.client_id = f"{CLIENT_ID_PREFIX}knob_{random.randint(0, 1000)}"
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

        # Create the dial/knob
        self.temp_dial = QDial()
        self.temp_dial.setMinimum(16)  # Minimum comfortable temperature
        self.temp_dial.setMaximum(30)  # Maximum reasonable temperature
        self.temp_dial.setValue(22)    # Default temperature
        self.temp_dial.setNotchesVisible(True)
        self.temp_dial.setWrapping(False)
        self.temp_dial.valueChanged.connect(self.on_temp_changed)
        
        # Add some styling
        self.temp_dial.setStyleSheet("""
            QDial {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2196F3, stop:1 #4CAF50);
            }
        """)
        
        # Temperature display label
        self.temp_label = QLabel("22°C")
        self.temp_label.setAlignment(Qt.AlignCenter)
        self.temp_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        
        # Status label
        self.status_label = QLabel("Disconnected")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: red;")
        
        # Add widgets to layout
        layout.addWidget(QLabel("Set Temperature:"))
        layout.addWidget(self.temp_dial)
        layout.addWidget(self.temp_label)
        layout.addWidget(self.status_label)

        # Connect to broker
        try:
            self.status_label.setText("Connecting to broker...")
            self.mqtt_client.connect(BROKER_IP, BROKER_PORT)
            self.mqtt_client.loop_start()
        except Exception as e:
            self.status_label.setText(f"Connection Error: {str(e)}")
            print(f"Connection Error: {str(e)}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.status_label.setText("Connected to broker")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            print("Knob Emulator connected to broker")
            # Publish initial setpoint
            self.publish_setpoint(self.temp_dial.value())
        else:
            self.status_label.setText(f"Connection failed with code {rc}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        self.status_label.setText("Disconnected from broker")
        self.status_label.setStyleSheet("color: red;")
        print("Knob Emulator disconnected from broker")

    def on_temp_changed(self, value):
        self.temp_label.setText(f"{value}°C")
        self.publish_setpoint(value)

    def publish_setpoint(self, temperature):
        if not self.connected:
            self.status_label.setText("Not connected to broker")
            return

        # Get current timestamp
        timestamp = datetime.now().isoformat()

        payload = json.dumps({
            "value": temperature,
            "unit": "celsius",
            "controller_id": self.client_id,
            "timestamp": timestamp
        })
        
        print(f"Publishing setpoint: {temperature}°C")
        self.mqtt_client.publish(SETPOINT_TOPIC, payload, qos=1)
        self.status_label.setText(f"Published: {temperature}°C")
        self.status_label.setStyleSheet("color: green;")

    def closeEvent(self, event):
        print("Shutting down Knob Emulator")
        self.mqtt_client.loop_stop()
        if self.connected:
            self.mqtt_client.disconnect()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show window
    window = KnobEmulator()
    window.show()
    
    sys.exit(app.exec_())
