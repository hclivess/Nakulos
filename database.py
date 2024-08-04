import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, config):
        self.config = config
        self.conn = None

    def connect(self):
        if self.conn is None:
            try:
                self.conn = psycopg2.connect(
                    host=self.config['host'],
                    database=self.config['database_name'],
                    user=self.config['username'],
                    password=self.config['password'],
                    port=self.config['port']
                )
                logger.info("Database connection established")
            except (Exception, psycopg2.Error) as error:
                logger.error(f"Error while connecting to PostgreSQL: {error}")
                raise

    @contextmanager
    def get_cursor(self):
        if self.conn is None:
            self.connect()
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

db = None


def init_db(config):
    global db
    db = Database(config)
    db.connect()

    # Create tables if they don't exist
    with db.get_cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hosts (
                id SERIAL PRIMARY KEY,
                hostname VARCHAR(255) UNIQUE NOT NULL,
                alias VARCHAR(255),
                location VARCHAR(255)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id SERIAL PRIMARY KEY,
                host_id INTEGER REFERENCES hosts(id),
                metric_name VARCHAR(255) NOT NULL,
                timestamp FLOAT NOT NULL,
                value FLOAT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                host_id INTEGER REFERENCES hosts(id),
                metric_name VARCHAR(255) NOT NULL,
                condition VARCHAR(50) NOT NULL,
                threshold FLOAT NOT NULL,
                duration INTEGER NOT NULL,
                enabled BOOLEAN DEFAULT TRUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downtimes (
                id SERIAL PRIMARY KEY,
                host_id INTEGER REFERENCES hosts(id),
                start_time FLOAT NOT NULL,
                end_time FLOAT NOT NULL
            )
        ''')
        db.conn.commit()


def get_db():
    return db