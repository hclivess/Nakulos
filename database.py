import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import logging
from contextlib import contextmanager
import json

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

def create_database_if_not_exists(config):
    conn = None
    try:
        conn = psycopg2.connect(
            host=config['host'],
            database='postgres',  # Connect to the default database
            user=config['username'],
            password=config['password'],
            port=config['port']
        )
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s"),
                [config['database_name']]
            )
            exists = cursor.fetchone()
            if not exists:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(config['database_name'])
                ))
                logger.info(f"Database {config['database_name']} created")
            else:
                logger.info(f"Database {config['database_name']} already exists")
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error while creating database: {error}")
        raise
    finally:
        if conn:
            conn.close()

db = None

def init_db(config):
    global db
    create_database_if_not_exists(config)
    db = Database(config)
    db.connect()

    # Create tables if they don't exist
    with db.get_cursor() as cursor:
        tables = [
            ("hosts", '''
                CREATE TABLE IF NOT EXISTS hosts (
                    id SERIAL PRIMARY KEY,
                    hostname VARCHAR(255) UNIQUE NOT NULL,
                    tags JSONB
                )
            '''),
            ("metrics", '''
                CREATE TABLE IF NOT EXISTS metrics (
                    id SERIAL PRIMARY KEY,
                    host_id INTEGER REFERENCES hosts(id) ON DELETE CASCADE,
                    metric_name VARCHAR(255) NOT NULL,
                    timestamp FLOAT NOT NULL,
                    value JSONB NOT NULL,
                    message TEXT
                )
            '''),
            ("alerts", '''
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    host_id INTEGER REFERENCES hosts(id) ON DELETE CASCADE,
                    metric_name VARCHAR(255) NOT NULL,
                    condition VARCHAR(50) NOT NULL,
                    threshold FLOAT NOT NULL,
                    duration INTEGER NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE
                )
            '''),
            ("downtimes", '''
                CREATE TABLE IF NOT EXISTS downtimes (
                    id SERIAL PRIMARY KEY,
                    host_id INTEGER REFERENCES hosts(id) ON DELETE CASCADE,
                    start_time FLOAT NOT NULL,
                    end_time FLOAT NOT NULL
                )
            '''),
            ("alert_history", '''
                CREATE TABLE IF NOT EXISTS alert_history (
                    id SERIAL PRIMARY KEY,
                    host_id INTEGER REFERENCES hosts(id) ON DELETE CASCADE,
                    alert_id INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
                    timestamp FLOAT NOT NULL,
                    value JSONB NOT NULL
                )
            '''),
            ("client_configs", '''
                CREATE TABLE IF NOT EXISTS client_configs (
                    client_id VARCHAR(255) PRIMARY KEY,
                    hostname VARCHAR(255) NOT NULL,
                    config JSONB NOT NULL,
                    tags JSONB,
                    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            '''),
            ("metric_scripts", '''
                CREATE TABLE IF NOT EXISTS metric_scripts (
                    name VARCHAR(255) PRIMARY KEY,
                    code TEXT NOT NULL,
                    tags JSONB
                )
            '''),
            ("users", '''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(60) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        ]

        for table_name, create_statement in tables:
            try:
                cursor.execute(create_statement)
                logger.info(f"Table '{table_name}' created or already exists.")
            except Exception as e:
                logger.error(f"Error creating table '{table_name}': {str(e)}")

    logger.info("All necessary tables have been processed")

def get_db():
    return db

def load_config(config_path='server_config.json'):
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {config_path}")
        raise

def setup_database():
    config = load_config()
    init_db(config['database'])
    logger.info("Database setup completed")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_database()