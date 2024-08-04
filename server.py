import tornado.ioloop
import tornado.web
from tornado.options import define, options
import json
import logging
from routes import make_app
from database import init_db, get_db
from queue_manager import MetricProcessor
from data_aggregator import aggregate_data

# Define command-line options
define("port", default=8888, help="run on the given port", type=int)
define("config", default="server_config.json", help="path to config file", type=str)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(config_path):
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {config_path}")
        raise

def main():
    # Parse command-line options
    tornado.options.parse_command_line()

    # Load configuration
    config = load_config(options.config)
    logger.info(f"Loaded configuration from {options.config}")

    # Initialize database
    try:
        init_db(config['database'])
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return

    # Initialize metric processor
    metric_processor = MetricProcessor(num_workers=config.get('num_workers', 3))
    metric_processor.start()
    logger.info(f"Started metric processor with {metric_processor.num_workers} workers")

    # Create Tornado application
    app = make_app(metric_processor)

    # Set up periodic callback for data aggregation (run daily)
    aggregation_callback = tornado.ioloop.PeriodicCallback(aggregate_data, 24 * 60 * 60 * 1000)  # 24 hours in milliseconds
    aggregation_callback.start()

    # Start the server
    app.listen(options.port)
    logger.info(f"Server started on http://localhost:{options.port}")

    # Start the IOLoop
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping server...")
    finally:
        # Cleanup
        metric_processor.stop()
        aggregation_callback.stop()
        db = get_db()
        if db:
            db.close()
        logger.info("Server stopped")

if __name__ == "__main__":
    main()