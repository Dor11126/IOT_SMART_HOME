import sqlite3
import threading
from datetime import datetime

class Database:
    """
    Database handler for Smart AC Control System.
    Stores temperature, humidity, setpoint readings and alarm messages.
    Thread-safe operations with locking mechanism.
    """
    
    def __init__(self, db_file="ac_control.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_file = db_file
        self.lock = threading.Lock()
        
        with self.lock:
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
            self.db_executor = self.conn.cursor()
            
            # Create readings table if it doesn't exist
            self.db_executor.execute('''
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    setpoint REAL,
                    ac_status INTEGER
                )
            ''')
            
            # Create alarms table if it doesn't exist
            self.db_executor.execute('''
                CREATE TABLE IF NOT EXISTS alarms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            ''')
            
            self.conn.commit()
    
    def insert_reading(self, temperature=None, humidity=None, setpoint=None, ac_status=None):
        """Insert a new sensor reading into the database."""
        timestamp = datetime.now().isoformat()
        
        with self.lock:
            self.db_executor.execute(
                """
                INSERT INTO readings (timestamp, temperature, humidity, setpoint, ac_status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (timestamp, temperature, humidity, setpoint, ac_status)
            )
            self.conn.commit()
    
    def insert_alarm(self, message):
        """Insert a new alarm message into the database."""
        timestamp = datetime.now().isoformat()
        
        with self.lock:
            self.db_executor.execute(
                """
                INSERT INTO alarms (timestamp, message)
                VALUES (?, ?)
                """,
                (timestamp, message)
            )
            self.conn.commit()
    
    def get_recent_readings(self, limit=100):
        """Get most recent readings from the database."""
        with self.lock:
            self.db_executor.execute(
                """
                SELECT timestamp, temperature, humidity, setpoint, ac_status
                FROM readings
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            )
            return self.db_executor.fetchall()
    
    def get_recent_alarms(self, limit=100):
        """Get most recent alarms from the database."""
        with self.lock:
            self.db_executor.execute(
                """
                SELECT timestamp, message, id
                FROM alarms
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            )
            return self.db_executor.fetchall()
    
    def close(self):
        """Close the database connection."""
        with self.lock:
            self.conn.close()
