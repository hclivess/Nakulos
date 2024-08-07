import pika
import json
import logging
from database import init_db, get_db
from models import Host, Metric, Alert
from sqlalchemy import func

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    with open('server_config.json', 'r') as config_file:
        return json.load(config_file)

config = load_config()

# Initialize database connection
init_db(config['database'])

def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        process_metric(data)
    except json.JSONDecodeError:
        logger.error("Received invalid JSON data")
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")

def process_metric(data):
    db = next(get_db())
    try:
        hostname = data['hostname']
        metrics = data['metrics']

        host = db.query(Host).filter(Host.hostname == hostname).first()
        if not host:
            logger.error(f"Host not found: {hostname}")
            return

        for metric_name, value in metrics.items():
            # Check alerts
            alerts = db.query(Alert).filter(Alert.host_id == host.id,
                                            Alert.metric_name == metric_name,
                                            Alert.enabled == True).all()
            for alert in alerts:
                if check_alert_condition(alert, value):
                    trigger_alert(alert, host, metric_name, value)
    finally:
        db.close()

def check_alert_condition(alert, value):
    if alert.condition == 'above':
        return value > alert.threshold
    elif alert.condition == 'below':
        return value < alert.threshold
    return False

def trigger_alert(alert, host, metric_name, value):
    # Implement alert triggering logic (e.g., sending emails, pushing to notification service)
    logger.info(f"Alert triggered for {host.hostname} - {metric_name}: {value}")
    # Here you would implement the actual alert notification logic

def main():
    # Set up RabbitMQ connection
    try:
        rabbitmq_config = config.get('rabbitmq', {})
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=rabbitmq_config.get('host', 'localhost'),
            port=rabbitmq_config.get('port', 5672),
            virtual_host=rabbitmq_config.get('virtual_host', '/'),
            credentials=pika.PlainCredentials(
                username=rabbitmq_config.get('username', 'guest'),
                password=rabbitmq_config.get('password', 'guest')
            )
        ))
        channel = connection.channel()
        channel.queue_declare(queue='metrics')
        channel.basic_consume(queue='metrics', on_message_callback=callback, auto_ack=True)

        logger.info("Worker started. Waiting for messages...")
        channel.start_consuming()
    except pika.exceptions.AMQPConnectionError:
        logger.error("Failed to connect to RabbitMQ. Please check your configuration and ensure RabbitMQ is running.")
    except KeyboardInterrupt:
        logger.info("Worker stopped.")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        if connection and not connection.is_closed:
            connection.close()

if __name__ == "__main__":
    main()