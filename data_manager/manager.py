import sys
import json
import random
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout,
                            QLabel, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QTimer
import paho.mqtt.client as mqtt

# Update import path to access mqtt_config from parent directory
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mqtt_config import (BROKER_IP, BROKER_PORT, USERNAME, PASSWORD,
                        TEMP_TOPIC, HUMIDITY_TOPIC, SETPOINT_TOPIC,
                        CONTROL_TOPIC, STATUS_TOPIC, ALARM_TOPIC,
                        CLIENT_ID_PREFIX)
from data_manager.db import Database

class DataManager(QMainWindow):
    """
    Smart AC Data Manager
    
    Manages temperature control logic, stores data in SQLite database,
    and provides a simple dashboard UI showing current status and alarms.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart AC Data Manager")
        self.setGeometry(100, 100, 800, 600)

        # Initialize variables
        self.current_temp = None
        self.current_humidity = None
        self.setpoint = None
        self.ac_status = False
        
        # Initialize database
        try:
            self.db = Database()
            self.log_direct("Database initialized")
        except Exception as e:
            print(f"Database initialization error: {e}")
            self.db = None
            self.log_direct("Database initialization failed!")

        # Initialize MQTT Client
        self.client_id = f"{CLIENT_ID_PREFIX}manager_{random.randint(0, 1000)}"
        self.mqtt_client = mqtt.Client(client_id=self.client_id)
        self.mqtt_client.username_pw_set(USERNAME, PASSWORD)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Status header
        header = QLabel("Smart AC Control System")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #2196F3;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Status section
        status_frame = QWidget()
        status_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px; padding: 10px;")
        status_layout = QVBoxLayout(status_frame)
        
        # Enlarge font for status labels
        status_font_style = "font-size: 18px; font-weight: bold;"
        
        self.temp_label = QLabel("Temperature: --°C")
        self.temp_label.setStyleSheet(status_font_style)
        self.humidity_label = QLabel("Humidity: --%")
        self.humidity_label.setStyleSheet(status_font_style)
        self.setpoint_label = QLabel("Setpoint: --°C")
        self.setpoint_label.setStyleSheet(status_font_style)
        self.ac_status_label = QLabel("AC Status: Unknown")
        self.ac_status_label.setStyleSheet(f"{status_font_style}; background-color: #9E9E9E; padding: 5px; border-radius: 5px; color: white;")
        
        for label in [self.temp_label, self.humidity_label, 
                     self.setpoint_label, self.ac_status_label]:
            status_layout.addWidget(label)
        
        layout.addWidget(status_frame)
        
        # Connection status label
        self.connection_label = QLabel("Connecting to broker...")
        self.connection_label.setAlignment(Qt.AlignCenter)
        self.connection_label.setStyleSheet("color: orange; font-weight: bold;")
        layout.addWidget(self.connection_label)

        # Create table for alarms
        alarms_label = QLabel("Recent Alarms:")
        alarms_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(alarms_label)
        
        self.alarm_table = QTableWidget()
        self.alarm_table.setColumnCount(2)
        self.alarm_table.setHorizontalHeaderLabels(["Timestamp", "Message"])
        self.alarm_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.alarm_table)
        
        # Add the debug log
        debug_label = QLabel("Debug Log:")
        debug_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(debug_label)
        
        self.debug_table = QTableWidget()
        self.debug_table.setColumnCount(1)
        self.debug_table.setHorizontalHeaderLabels(["Message"])
        self.debug_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.debug_table)

        # Connect to broker
        try:
            self.mqtt_client.connect(BROKER_IP, BROKER_PORT)
            self.mqtt_client.loop_start()
            self.log_direct("MQTT connection started...")
        except Exception as e:
            self.connection_label.setText(f"Connection Error: {str(e)}")
            self.connection_label.setStyleSheet("color: red; font-weight: bold;")
            self.log_direct(f"MQTT connection error: {str(e)}")

        # Timer for periodic UI updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(5000)  # Update every 5 seconds

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            # Subscribe to all relevant topics
            topics = [
                (TEMP_TOPIC, 1),
                (HUMIDITY_TOPIC, 1),
                (SETPOINT_TOPIC, 1),
                (STATUS_TOPIC, 1)
            ]
            self.mqtt_client.subscribe(topics)
            self.connection_label.setText("Connected to broker")
            self.connection_label.setStyleSheet("color: green; font-weight: bold;")
            self.log_alarm("Data Manager connected to broker")
        else:
            self.connection_label.setText(f"Connection failed with code {rc}")
            self.connection_label.setStyleSheet("color: red; font-weight: bold;")
            self.log_direct(f"MQTT connection failed with code: {rc}")

    def on_disconnect(self, client, userdata, rc):
        self.connection_label.setText("Disconnected from broker")
        self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        self.log_alarm("Data Manager disconnected from broker")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            self.log_direct(f"Received on {msg.topic}: {payload}")
            
            if msg.topic == TEMP_TOPIC:
                self.current_temp = payload.get("value")
                self.log_direct(f"Updated temperature: {self.current_temp}°C")
                self.handle_temperature_update(self.current_temp)
                
            elif msg.topic == HUMIDITY_TOPIC:
                self.current_humidity = payload.get("value")
                self.log_direct(f"Updated humidity: {self.current_humidity}%")
                
            elif msg.topic == SETPOINT_TOPIC:
                self.setpoint = payload.get("value")
                self.log_direct(f"Updated setpoint: {self.setpoint}°C")
                # Check if we need to update AC state based on new setpoint
                self.handle_temperature_update(self.current_temp)
                
            elif msg.topic == STATUS_TOPIC:
                old_status = self.ac_status
                state = payload.get("state", "")
                self.ac_status = (state.lower() == "on")
                self.log_direct(f"Updated AC status: {self.ac_status}")
                
                if old_status != self.ac_status:
                    status_text = "ON" if self.ac_status else "OFF"
                    self.log_alarm(f"AC status changed to: {status_text}")
            
            # Store reading in database
            if self.db is not None and self.current_temp is not None:
                try:
                    self.db.insert_reading(
                        temperature=self.current_temp,
                        humidity=self.current_humidity,
                        setpoint=self.setpoint,
                        ac_status=1 if self.ac_status else 0
                    )
                except Exception as e:
                    print(f"Database insert error: {e}")
                    self.log_direct(f"Database insert error: {e}")
            
            # Update UI
            self.update_ui()
            
        except Exception as e:
            self.log_alarm(f"Error processing message: {str(e)}")
            self.log_direct(f"Message processing error: {str(e)}")

    def handle_temperature_update(self, temperature):
        if temperature is None or self.setpoint is None:
            self.log_direct(f"Skipping temp control - temp: {temperature}, setpoint: {self.setpoint}")
            return

        # Print current state
        self.log_direct(f"===== TEMPERATURE CONTROL =====")
        self.log_direct(f"Temperature: {temperature}°C")
        self.log_direct(f"Setpoint: {self.setpoint}°C")
        self.log_direct(f"AC Status: {'ON' if self.ac_status else 'OFF'}")

        # Check for high temperature alert
        if temperature >= 30:
            alert_msg = f"High temperature alert: {temperature}°C"
            self.log_direct(alert_msg)
            self.log_alarm(alert_msg)

        # Calculate temperature difference
        temp_difference = float(temperature) - float(self.setpoint)
        self.log_direct(f"Temperature difference: {temp_difference:.1f}°C")

        # Control logic with hysteresis
        if temp_difference >= 5 and not self.ac_status:
            # Turn AC ON if temp is 5 degrees or more above setpoint
            message = f"Auto-activating AC: Temperature ({temperature}°C) is {temp_difference:.1f}°C above setpoint ({self.setpoint}°C)"
            self.log_direct(f"DECISION: {message}")
            self.log_alarm(message)
            self.publish_ac_command("on")
            self.ac_status = True
            # Update UI immediately
            self.ac_status_label.setText("AC Status: ON")
            self.log_direct("AC TURNED ON")
        elif temp_difference <= -1 and self.ac_status:
            # Turn AC OFF if temp is 1 degree below setpoint (hysteresis)
            message = f"Auto-deactivating AC: Temperature ({temperature}°C) is below setpoint ({self.setpoint}°C)"
            self.log_direct(f"DECISION: {message}")
            self.log_alarm(message)
            self.publish_ac_command("off")
            self.ac_status = False
            # Update UI immediately
            self.ac_status_label.setText("AC Status: OFF")
            self.log_direct("AC TURNED OFF")
        else:
            self.log_direct(f"DECISION: No action needed - conditions not met for state change")

        # Force the AC on for very high temperatures regardless of other conditions
        if temperature >= 35 and not self.ac_status:
            message = f"EMERGENCY: Force turning AC ON due to very high temperature: {temperature}°C"
            self.log_direct(message)
            self.log_alarm(message)
            self.publish_ac_command("on")
            self.ac_status = True
            # Update UI immediately
            self.ac_status_label.setText("AC Status: ON")
            self.log_direct("EMERGENCY AC ACTIVATION")

        self.log_direct("=================================")

    def publish_ac_command(self, command):
        try:
            self.log_direct(f"***** PUBLISHING AC COMMAND: {command} *****")
            
            payload = json.dumps({
                "command": command,
                "timestamp": datetime.now().isoformat()
            })
            
            result = self.mqtt_client.publish(CONTROL_TOPIC, payload, qos=1)
            self.log_direct(f"Command published. Result: {result}")
            self.log_alarm(f"Sent AC command: {command}")
        except Exception as e:
            error_msg = f"Error publishing AC command: {str(e)}"
            self.log_direct(error_msg)
            self.log_alarm(error_msg)

    def log_alarm(self, message):
        """Log important system alerts to database and MQTT"""
        timestamp = datetime.now().isoformat()
        
        # Store in database
        if self.db is not None:
            try:
                self.db.insert_alarm(message)
            except Exception as e:
                print(f"Error logging alarm to database: {e}")
        
        # Publish to MQTT
        try:
            payload = json.dumps({
                "message": message,
                "timestamp": timestamp
            })
            self.mqtt_client.publish(ALARM_TOPIC, payload, qos=1)
        except Exception as e:
            print(f"Error publishing alarm: {e}")
        
        # Update UI
        self.update_alarms_table()
        
        # Also log to debug
        self.log_direct(f"ALARM: {message}")

    def log_direct(self, message):
        """Add a message to the debug log (not stored in database)"""
        # Print to console
        print(message)
        
        # Only add to debug table if it exists
        if hasattr(self, 'debug_table') and self.debug_table is not None:
            # Add to debug table
            row_position = self.debug_table.rowCount()
            self.debug_table.insertRow(row_position)
            self.debug_table.setItem(row_position, 0, QTableWidgetItem(message))
            
            # Scroll to bottom
            self.debug_table.scrollToBottom()
            
            # Keep only the last 100 messages
            if self.debug_table.rowCount() > 100:
                self.debug_table.removeRow(0)

    def update_ui(self):
        """Update the UI with current system status"""
        # Update status labels
        status_font_style = "font-size: 18px; font-weight: bold;"
        
        if self.current_temp is not None:
            self.temp_label.setText(f"Temperature: {self.current_temp}°C")
            self.temp_label.setStyleSheet(status_font_style)
        if self.current_humidity is not None:
            self.humidity_label.setText(f"Humidity: {self.current_humidity}%")
            self.humidity_label.setStyleSheet(status_font_style)
        if self.setpoint is not None:
            self.setpoint_label.setText(f"Setpoint: {self.setpoint}°C")
            self.setpoint_label.setStyleSheet(status_font_style)
        
        # Set AC status with color
        self.ac_status_label.setText(f"AC Status: {'ON' if self.ac_status else 'OFF'}")
        if self.ac_status:
            self.ac_status_label.setStyleSheet(f"{status_font_style}; background-color: #4CAF50; padding: 5px; border-radius: 5px; color: white;")
        else:
            self.ac_status_label.setStyleSheet(f"{status_font_style}; background-color: #F44336; padding: 5px; border-radius: 5px; color: white;")
        
        # Update alarms table
        self.update_alarms_table()

    def update_alarms_table(self):
        """Update the alarms table with recent alarms from database"""
        if self.db is not None:
            try:
                alarms = self.db.get_recent_alarms(10)  # Get last 10 alarms
                
                # Clear existing rows
                self.alarm_table.setRowCount(0)
                
                # Add new rows
                for i, (timestamp, message, _) in enumerate(alarms):
                    self.alarm_table.insertRow(i)
                    self.alarm_table.setItem(i, 0, QTableWidgetItem(timestamp))
                    self.alarm_table.setItem(i, 1, QTableWidgetItem(message))
            except Exception as e:
                print(f"Error updating alarms table: {e}")
                self.log_direct(f"Error updating alarms table: {e}")

    def closeEvent(self, event):
        """Clean up resources when closing the application"""
        self.log_direct("Shutting down Data Manager")
        self.update_timer.stop()
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        if self.db is not None:
            self.db.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show window
    window = DataManager()
    window.show()
    
    sys.exit(app.exec_())
