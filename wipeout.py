import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_config():
    try:
        with open('server_config.json', 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        logger.error("Config file not found. Please ensure server_config.json exists.")
        return None
    except json.JSONDecodeError:
        logger.error("Invalid JSON in config file. Please check server_config.json.")
        return None


def wipeout_database():
    config = load_config()
    if not config:
        return

    db_config = config['database']

    try:
        # Connect to the default PostgreSQL database
        conn = psycopg2.connect(
            host=db_config['host'],
            user=db_config['username'],
            password=db_config['password'],
            dbname='postgres'  # Connect to the default 'postgres' database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with conn.cursor() as cursor:
            # Check if the database exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_config['database_name'],))
            exists = cursor.fetchone()

            if exists:
                # Terminate all connections to the database
                cursor.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = %s AND pid <> pg_backend_pid()
                """, (db_config['database_name'],))

                # Drop the database
                cursor.execute(f"DROP DATABASE {db_config['database_name']}")
                logger.info(f"Database '{db_config['database_name']}' has been deleted.")
            else:
                logger.info(f"Database '{db_config['database_name']}' does not exist.")

    except psycopg2.Error as e:
        logger.error(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    wipeout_database()