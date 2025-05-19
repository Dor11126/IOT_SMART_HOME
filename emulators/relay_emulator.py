import sys
import random
import json
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout,
                            QLabel, QGraphicsDropShadowEffect, QPushButton)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtGui import QColor
import paho.mqtt.client as mqtt

# Update import path to access mqtt_config from parent directory
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mqtt_config import (BROKER_IP, BROKER_PORT, USERNAME, PASSWORD,
                        CONTROL_TOPIC, STATUS_TOPIC, CLIENT_ID_PREFIX)

class RelayEmulator(QMainWindow):
    """AC Relay Emulator that simulates turning the AC on and off"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AC Relay Status")
        self.setGeometry(100, 100, 350, 450)
        self.setStyleSheet("background-color: #f5f5f5;")
        
        # Initialize state
        self.state = False  # False = OFF, True = ON
        self.animation_running = False  # Track if animation is running
        
        # Initialize MQTT Client
        self.client_id = f"{CLIENT_ID_PREFIX}relay_{random.randint(0, 1000)}"
        self.mqtt_client = mqtt.Client(client_id=self.client_id)
        self.mqtt_client.username_pw_set(USERNAME, PASSWORD)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.connected = False

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title label
        title_label = QLabel("AC Relay Status")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #1565C0;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Description label
        desc_label = QLabel("This emulator represents the AC relay control")
        desc_label.setStyleSheet("font-size: 14px; color: #555;")
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        # Create status indicator
        self.status_container = QWidget()
        self.status_container.setFixedSize(180, 180)
        
        # Container for shadow effect
        status_layout = QVBoxLayout(self.status_container)
        status_layout.setAlignment(Qt.AlignCenter)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create inner circle
        self.status_circle = QWidget(self.status_container)
        self.status_circle.setFixedSize(150, 150)
        self.status_circle.setStyleSheet("background-color: #ff4444; border-radius: 75px;")
        
        # Apply shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 2)
        self.status_circle.setGraphicsEffect(shadow)
        
        status_layout.addWidget(self.status_circle)
        
        # Status label
        self.status_label = QLabel("OFF")
        self.status_label.setParent(self.status_circle)
        self.status_label.setGeometry(0, 0, 150, 150)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: white;
        """)
        
        # Add toggle button
        self.toggle_button = QPushButton("Toggle AC")
        self.toggle_button.setFixedSize(150, 40)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_relay)
        self.toggle_button.setEnabled(False)  # Enabled when connected

        # Connection status panel
        connection_panel = QWidget()
        connection_panel.setStyleSheet("background-color: white; border-radius: 10px;")
        
        # Apply shadow to the panel
        panel_shadow = QGraphicsDropShadowEffect()
        panel_shadow.setBlurRadius(10)
        panel_shadow.setColor(QColor(0, 0, 0, 50))
        panel_shadow.setOffset(0, 2)
        connection_panel.setGraphicsEffect(panel_shadow)
        
        connection_layout = QVBoxLayout(connection_panel)
        
        # Connection status
        self.connection_label = QLabel("Disconnected")
        self.connection_label.setAlignment(Qt.AlignCenter)
        self.connection_label.setStyleSheet("color: #D32F2F; font-size: 16px; font-weight: bold;")
        connection_layout.addWidget(self.connection_label)
        
        # Add widgets to main layout
        layout.addWidget(self.status_container, alignment=Qt.AlignCenter)
        layout.addWidget(self.toggle_button, alignment=Qt.AlignCenter)
        layout.addWidget(connection_panel)

        # Connect to broker
        try:
            self.connection_label.setText("Connecting to broker...")
            self.mqtt_client.connect(BROKER_IP, BROKER_PORT)
            self.mqtt_client.loop_start()
        except Exception as e:
            self.connection_label.setText(f"Connection Error: {str(e)}")
            print(f"Connection Error: {str(e)}")
            
    def toggle_relay(self):
        """Toggle the relay state when button is clicked"""
        if self.state:
            self.set_state(False)  # Turn OFF
        else:
            self.set_state(True)   # Turn ON
            
        # Publish the command
        command = "on" if self.state else "off"
        payload = json.dumps({
            "command": command,
            "timestamp": datetime.now().isoformat()
        })
        self.mqtt_client.publish(CONTROL_TOPIC, payload, qos=1)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.connection_label.setText("Connected to broker")
            self.connection_label.setStyleSheet("color: #388E3C; font-size: 16px; font-weight: bold;")
            self.mqtt_client.subscribe([(CONTROL_TOPIC, 1)])
            self.toggle_button.setEnabled(True)  # Enable toggle button when connected
            print("Relay Emulator connected to broker")
            # Publish initial state
            self.publish_state()
        else:
            self.connection_label.setText(f"Connection failed with code {rc}")
            self.connection_label.setStyleSheet("color: #D32F2F; font-size: 16px; font-weight: bold;")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        self.connection_label.setText("Disconnected from broker")
        self.connection_label.setStyleSheet("color: #D32F2F; font-size: 16px; font-weight: bold;")
        self.toggle_button.setEnabled(False)  # Disable toggle button when disconnected
        print("Relay Emulator disconnected from broker")

    def on_message(self, client, userdata, msg):
        try:
            print(f"Relay received message on topic {msg.topic}: {msg.payload.decode()}")
            payload = json.loads(msg.payload.decode())
            
            if msg.topic == CONTROL_TOPIC:
                command = payload.get("command", "").lower()
                print(f"Relay command received: {command}")
                
                if command == "on":
                    self.set_state(True)
                    print("Relay turning ON")
                elif command == "off":
                    self.set_state(False)
                    print("Relay turning OFF")
                else:
                    print(f"Unknown command: {command}")
                
        except Exception as e:
            print(f"Error processing message: {str(e)}")

    def set_state(self, new_state):
        """Set relay state and update UI immediately"""
        # Only update if state has changed or no animation is running
        if new_state != self.state or not self.animation_running:
            self.state = new_state
            
            # Update UI immediately
            if self.state:
                # Update UI for ON state
                self.status_label.setText("ON")
                self.status_circle.setStyleSheet("background-color: #4CAF50; border-radius: 75px;")
            else:
                # Update UI for OFF state
                self.status_label.setText("OFF")
                self.status_circle.setStyleSheet("background-color: #ff4444; border-radius: 75px;")
            
            # Create animation for feedback (only if not already running)
            if not self.animation_running:
                self.animate_status_change()
            
            # Publish new state
            self.publish_state()
        
    def animate_status_change(self):
        """Animate the status change for visual feedback"""
        # Prevent multiple animations running at once
        if self.animation_running:
            return
            
        self.animation_running = True
            
        # Create animation for smooth transition
        self.animation = QPropertyAnimation(self.status_circle, b"size")
        self.animation.setDuration(150)
        self.animation.setStartValue(QSize(150, 150))
        self.animation.setEndValue(QSize(130, 130))
        self.animation.setEasingCurve(QEasingCurve.OutQuad)
        
        # Connect animation finished signal
        self.animation.finished.connect(self.animation_step2)
        self.animation.start()
        
    def animation_step2(self):
        """Second step of the animation"""
        # Animate back to original size
        self.animation2 = QPropertyAnimation(self.status_circle, b"size")
        self.animation2.setDuration(300)
        self.animation2.setStartValue(QSize(130, 130))
        self.animation2.setEndValue(QSize(150, 150))
        self.animation2.setEasingCurve(QEasingCurve.OutBounce)
        self.animation2.finished.connect(self.animation_completed)
        self.animation2.start()
        
    def animation_completed(self):
        """Called when animation sequence is completed"""
        self.animation_running = False

    def publish_state(self):
        if not self.connected:
            return
            
        status = "on" if self.state else "off"
        print(f"Publishing relay state: {status}")
        
        payload = json.dumps({
            "state": status,
            "relay_id": self.client_id,
            "timestamp": datetime.now().isoformat()
        })
        self.mqtt_client.publish(STATUS_TOPIC, payload, qos=1)

    def closeEvent(self, event):
        print("Shutting down Relay Emulator")
        self.mqtt_client.loop_stop()
        if self.connected:
            self.mqtt_client.disconnect()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show window
    window = RelayEmulator()
    window.show()
    
    sys.exit(app.exec_())
