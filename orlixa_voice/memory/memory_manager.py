import sqlite3
import os
from utils.logger import get_logger

logger = get_logger()

class MemoryManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self._initialize_db()

    def _initialize_db(self):
        try:
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)

            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()

            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    command TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    info TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')

            self.conn.commit()
            logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def log_command(self, command, status):
        try:
            cursor = self.conn.cursor()
            cursor.execute('INSERT INTO command_history (command, status) VALUES (?, ?)', (command, status))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error logging command to DB: {e}")

    def save_preference(self, key, value):
        try:
            cursor = self.conn.cursor()
            cursor.execute('REPLACE INTO preferences (key, value) VALUES (?, ?)', (key, value))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error saving preference: {e}")

    def get_preference(self, key):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT value FROM preferences WHERE key = ?', (key,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error getting preference: {e}")
            return None

    def close(self):
        if self.conn:
            self.conn.close()
