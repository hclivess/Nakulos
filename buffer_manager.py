import sqlite3
import json
import logging

logger = logging.getLogger(__name__)

class BufferManager:
    def __init__(self, config_manager, buffer_size=1000, db_path='metric_buffer.db'):
        self.config_manager = config_manager
        self.buffer_size = buffer_size
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            ''')

    def add(self, data):
        with self.conn:
            self.conn.execute('INSERT INTO metrics (data, timestamp) VALUES (?, ?)',
                              (json.dumps(data), time.time()))
        self.trim_buffer()

    def get_all(self):
        with self.conn:
            cursor = self.conn.execute('SELECT id, data, timestamp FROM metrics ORDER BY timestamp')
            return cursor.fetchall()

    def remove(self, ids):
        with self.conn:
            self.conn.executemany('DELETE FROM metrics WHERE id = ?', [(id,) for id in ids])

    def trim_buffer(self):
        with self.conn:
            count = self.conn.execute('SELECT COUNT(*) FROM metrics').fetchone()[0]
            if count > self.buffer_size:
                excess = count - self.buffer_size
                self.conn.execute(
                    f'DELETE FROM metrics WHERE id IN (SELECT id FROM metrics ORDER BY timestamp LIMIT {excess})')

    def close(self):
        self.conn.close()