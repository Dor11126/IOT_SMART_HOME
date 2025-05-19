import sys
import os
import subprocess
import time
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPixmap

class ComponentThread(QThread):
    signal = pyqtSignal(str)
    
    def __init__(self, name, script, parent=None):
        super().__init__(parent)
        self.name = name
        self.script = script
        self.process = None
        
    def run(self):
        try:
            self.process = subprocess.Popen(
                ["python", self.script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.signal.emit(f"{self.name} started")
            
            # Monitor process output
            for line in self.process.stdout:
                self.signal.emit(f"{self.name}: {line.strip()}")
                
        except Exception as e:
            self.signal.emit(f"{self.name} error: {str(e)}")
            
    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.signal.emit(f"{self.name} stopped")


class SmartACLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Smart AC Control System")
        self.setGeometry(100, 100, 800, 500)
        self.setStyleSheet("background-color: #f0f0f0;")
        
        # Initialize components
        self.components = []
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("Smart AC Control System")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)
        
        # Description
        description = QLabel("IoT-based air conditioning control system with temperature monitoring")
        description.setStyleSheet("font-size: 14px; color: #555;")
        description.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(description)
        
        # Component controls
        components_group = QGroupBox("System Components")
        components_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        components_layout = QVBoxLayout(components_group)
        
        # Add component controls with updated script paths
        components = [
            {"name": "Data Manager", "script": "data_manager/manager.py", "description": "Central control and data storage"},
            {"name": "DHT Emulator", "script": "emulators/dht_emulator.py", "description": "Temperature and humidity sensor"},
            {"name": "Knob Emulator", "script": "emulators/knob_emulator.py", "description": "Temperature setpoint control"},
            {"name": "Relay Emulator", "script": "emulators/relay_emulator.py", "description": "AC power control relay"}
        ]
        
        for component in components:
            component_widget = self.create_component_widget(component)
            components_layout.addWidget(component_widget)
        
        main_layout.addWidget(components_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.start_all_btn = QPushButton("Start All Components")
        self.start_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_all_btn.clicked.connect(self.start_all_components)
        
        self.stop_all_btn = QPushButton("Stop All Components")
        self.stop_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.stop_all_btn.clicked.connect(self.stop_all_components)
        self.stop_all_btn.setEnabled(False)
        
        action_layout.addWidget(self.start_all_btn)
        action_layout.addWidget(self.stop_all_btn)
        
        main_layout.addLayout(action_layout)
        
        # Status log
        self.log_label = QLabel("Status Log:")
        self.log_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(self.log_label)
        
        self.status_log = QLabel("Ready to start components...")
        self.status_log.setStyleSheet("""
            background-color: white;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        """)
        self.status_log.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.status_log.setWordWrap(True)
        self.status_log.setMinimumHeight(100)
        main_layout.addWidget(self.status_log)
        
    def create_component_widget(self, component):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Component info
        info_layout = QVBoxLayout()
        name_label = QLabel(component["name"])
        name_label.setStyleSheet("font-weight: bold;")
        desc_label = QLabel(component["description"])
        desc_label.setStyleSheet("color: #555; font-style: italic;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        
        # Start button for this component
        btn = QPushButton("Start")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        
        # Create a closure to capture the component details
        def start_component():
            self.start_component(component)
            btn.setText("Running")
            btn.setEnabled(False)
            
        btn.clicked.connect(start_component)
        component["button"] = btn
        
        layout.addLayout(info_layout)
        layout.addWidget(btn, alignment=Qt.AlignRight)
        
        return widget
        
    def log_status(self, message):
        current_text = self.status_log.text()
        lines = current_text.split("\n")
        if len(lines) > 10:  # Keep log limited
            lines = lines[-10:]
        
        lines.append(message)
        self.status_log.setText("\n".join(lines))
        
    def start_component(self, component):
        thread = ComponentThread(component["name"], component["script"])
        thread.signal.connect(self.log_status)
        thread.start()
        
        component["thread"] = thread
        self.components.append(component)
        
        self.log_status(f"Started {component['name']}")
        
        # Enable stop button once components are running
        self.stop_all_btn.setEnabled(True)
        
    def start_all_components(self):
        # Start in correct order with delays
        components = [
            {"name": "Data Manager", "script": "data_manager/manager.py", "description": "Central control and data storage"},
            {"name": "DHT Emulator", "script": "emulators/dht_emulator.py", "description": "Temperature and humidity sensor"},
            {"name": "Knob Emulator", "script": "emulators/knob_emulator.py", "description": "Temperature setpoint control"},
            {"name": "Relay Emulator", "script": "emulators/relay_emulator.py", "description": "AC power control relay"}
        ]
        
        # Disable start button during startup
        self.start_all_btn.setEnabled(False)
        self.start_all_btn.setText("Starting...")
        
        # Start Data Manager first
        self.start_component(components[0])
        time.sleep(3)  # Give manager time to initialize
        
        # Start the rest
        for component in components[1:]:
            self.start_component(component)
            time.sleep(1)
        
        self.log_status("All components started successfully")
        self.start_all_btn.setText("Components Running")
        
    def stop_all_components(self):
        for component in self.components:
            if "thread" in component:
                component["thread"].stop()
                component["button"].setText("Start")
                component["button"].setEnabled(True)
        
        self.components = []
        self.log_status("All components stopped")
        
        # Reset buttons
        self.start_all_btn.setEnabled(True)
        self.start_all_btn.setText("Start All Components")
        self.stop_all_btn.setEnabled(False)
        
    def closeEvent(self, event):
        # Stop all components when closing
        self.stop_all_components()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set app style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = SmartACLauncher()
    window.show()
    
    sys.exit(app.exec_())
