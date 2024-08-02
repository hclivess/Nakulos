import tornado.ioloop
import tornado.web
import json
import sqlite3
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Load email configuration
def load_email_config():
    try:
        with open('email_config.json', 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        print("Email configuration file not found. Email alerts will be disabled.")
        return None
    except json.JSONDecodeError:
        print("Invalid email configuration file. Email alerts will be disabled.")
        return None


EMAIL_CONFIG = load_email_config()

# Create a connection to the SQLite database
conn = sqlite3.connect('metrics.db', check_same_thread=False)
cursor = conn.cursor()

# Create the metrics table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS metrics
    (hostname TEXT, metric_name TEXT, timestamp REAL, value REAL, additional_data TEXT)
''')

# Create the alerts table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS alerts
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     hostname TEXT,
     metric_name TEXT,
     condition TEXT,
     threshold REAL,
     duration INTEGER,
     enabled INTEGER DEFAULT 1)
''')

# Create the downtimes table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS downtimes
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     hostname TEXT,
     start_time REAL,
     end_time REAL)
''')

conn.commit()


class MetricsStorage:
    def add_metrics(self, hostname, data, additional_data):
        timestamp = time.time()
        for metric, value in data.items():
            cursor.execute('''
                INSERT INTO metrics (hostname, metric_name, timestamp, value, additional_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (hostname, metric, timestamp, value, json.dumps(additional_data)))
        conn.commit()

    def get_latest_metrics(self):
        cursor.execute('''
            SELECT hostname, metric_name, MAX(timestamp), value, additional_data
            FROM metrics
            WHERE metric_name != 'alert_triggered'
            GROUP BY hostname, metric_name
        ''')
        results = cursor.fetchall()
        latest_metrics = {}
        for hostname, metric_name, timestamp, value, additional_data in results:
            if hostname not in latest_metrics:
                latest_metrics[hostname] = {'metrics': {}, 'additional_data': json.loads(additional_data)}
            latest_metrics[hostname]['metrics'][metric_name] = (timestamp, value)
        return latest_metrics

    def get_metric_history(self, hostname, metric_name, start, end):
        cursor.execute('''
            SELECT timestamp, value, additional_data
            FROM metrics
            WHERE hostname = ? AND metric_name = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        ''', (hostname, metric_name, start, end))
        return [(*row[:2], json.loads(row[2])) for row in cursor.fetchall()]

    def get_hosts(self):
        cursor.execute('''
            SELECT DISTINCT hostname, additional_data
            FROM metrics
            WHERE metric_name != 'alert_triggered'
        ''')
        return [{'hostname': row[0], 'additional_data': json.loads(row[1])} for row in cursor.fetchall()]

    def aggregate_and_cleanup(self):
        current_time = time.time()
        intervals = [
            (60, current_time - 24 * 3600),  # 1 minute for last 24 hours
            (300, current_time - 7 * 24 * 3600),  # 5 minutes for last 7 days
            (3600, current_time - 30 * 24 * 3600),  # 1 hour for last 30 days
            (86400, current_time - 90 * 24 * 3600),  # 1 day for last 90 days
            (7 * 86400, current_time - 365 * 24 * 3600)  # 1 week for last year
        ]

        for i, (interval, start_time) in enumerate(intervals):
            end_time = intervals[i - 1][1] if i > 0 else current_time

            cursor.execute('''
                INSERT INTO metrics (hostname, metric_name, timestamp, value, additional_data)
                SELECT hostname, metric_name, 
                       CAST(timestamp / ? AS INT) * ?, 
                       AVG(value),
                       additional_data
                FROM metrics
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY hostname, metric_name, CAST(timestamp / ? AS INT)
            ''', (interval, interval, start_time, end_time, interval))

            # Remove original data that has been aggregated
            if i > 0:  # Don't delete the most recent data
                cursor.execute('''
                    DELETE FROM metrics
                    WHERE timestamp BETWEEN ? AND ?
                      AND timestamp % ? != 0
                ''', (start_time, end_time, interval))

        # Remove data older than 1 year
        cursor.execute('''
            DELETE FROM metrics
            WHERE timestamp < ?
        ''', (current_time - 365 * 24 * 3600,))

        conn.commit()


metrics_storage = MetricsStorage()


class AlertManager:
    def __init__(self):
        self.alert_state = {}

    def get_alert_config(self, hostname, metric):
        cursor.execute('''
            SELECT condition, threshold, duration, enabled
            FROM alerts
            WHERE hostname IN (?, 'default') AND metric_name = ?
            ORDER BY CASE WHEN hostname = 'default' THEN 1 ELSE 0 END
            LIMIT 1
        ''', (hostname, metric))
        result = cursor.fetchone()
        if result:
            return {
                'condition': result[0],
                'threshold': result[1],
                'duration': result[2],
                'enabled': bool(result[3])
            }
        return None

    def check_alerts(self, hostname, metrics):
        if self.is_in_downtime(hostname):
            return

        current_time = time.time()
        for metric, value in metrics.items():
            alert_config = self.get_alert_config(hostname, metric)
            if alert_config and alert_config['enabled']:
                alert_key = f"{hostname}_{metric}"

                if self.check_threshold(value, alert_config):
                    if alert_key not in self.alert_state:
                        self.alert_state[alert_key] = current_time
                    elif current_time - self.alert_state[alert_key] >= alert_config['duration']:
                        self.send_alert(hostname, metric, value, alert_config)
                        del self.alert_state[alert_key]  # Reset the alert state
                else:
                    if alert_key in self.alert_state:
                        del self.alert_state[alert_key]

    def is_in_downtime(self, hostname):
        current_time = time.time()
        cursor.execute('''
            SELECT COUNT(*) FROM downtimes
            WHERE hostname = ? AND start_time <= ? AND end_time > ?
        ''', (hostname, current_time, current_time))
        return cursor.fetchone()[0] > 0

    def check_threshold(self, value, alert_config):
        if alert_config['condition'] == 'above':
            return value > alert_config['threshold']
        elif alert_config['condition'] == 'below':
            return value < alert_config['threshold']
        return False

    def send_alert(self, hostname, metric, value, alert_config):
        subject = f"Alert: {metric} on {hostname}"
        body = f"The {metric} on {hostname} is {alert_config['condition']} {alert_config['threshold']} (current value: {value})"
        print(f"ALERT: {subject} - {body}")

        # Log the alert as a special metric
        metrics_storage.add_metrics(hostname, {"alert_triggered": 1}, {
            "alert_metric": metric,
            "alert_value": value,
            "alert_condition": alert_config['condition'],
            "alert_threshold": alert_config['threshold']
        })

        # Send email alert if configuration is available
        if EMAIL_CONFIG:
            self.send_email_alert(subject, body)

    def send_email_alert(self, subject, body):
        if not EMAIL_CONFIG:
            print("Email configuration not available. Skipping email alert.")
            return

        message = MIMEMultipart()
        message["From"] = EMAIL_CONFIG["sender_email"]
        message["To"] = EMAIL_CONFIG["recipient_email"]
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
                server.starttls()
                server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
                server.send_message(message)
            print("Email alert sent successfully")
        except Exception as e:
            print(f"Failed to send email alert: {e}")


alert_manager = AlertManager()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Monitoring Server is running")


class MetricsHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        hostname = data['hostname']
        metrics = data['metrics']
        additional_data = data.get('additional_data', {})
        metrics_storage.add_metrics(hostname, metrics, additional_data)
        alert_manager.check_alerts(hostname, metrics)
        self.write({"status": "received"})


class FetchLatestHandler(tornado.web.RequestHandler):
    def get(self):
        latest_metrics = metrics_storage.get_latest_metrics()
        # Remove alert_triggered metrics from the response
        for host_metrics in latest_metrics.values():
            host_metrics['metrics'].pop('alert_triggered', None)
        self.write(json.dumps(latest_metrics))


class FetchHistoryHandler(tornado.web.RequestHandler):
    def get(self, hostname, metric_name):
        start = float(self.get_argument("start", 0))
        end = float(self.get_argument("end", time.time()))
        history = metrics_storage.get_metric_history(hostname, metric_name, start, end)
        self.write(json.dumps(history))


class FetchHostsHandler(tornado.web.RequestHandler):
    def get(self):
        hosts = metrics_storage.get_hosts()
        self.write(json.dumps(hosts))


class AlertConfigHandler(tornado.web.RequestHandler):
    def get(self):
        cursor.execute('SELECT id, hostname, metric_name, condition, threshold, duration, enabled FROM alerts')
        alerts = [
            {'id': row[0], 'hostname': row[1], 'metric_name': row[2], 'condition': row[3],
             'threshold': row[4], 'duration': row[5], 'enabled': bool(row[6])}
            for row in cursor.fetchall()]
        self.write(json.dumps(alerts))

    def post(self):
        data = json.loads(self.request.body)
        cursor.execute('''
            INSERT OR REPLACE INTO alerts (hostname, metric_name, condition, threshold, duration, enabled)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['hostname'], data['metric_name'], data['condition'], data['threshold'], data['duration'], 1))
        conn.commit()
        self.write({"status": "success"})

    def delete(self):
        data = json.loads(self.request.body)
        hostname = data['hostname']
        metric_name = data['metric_name']
        cursor.execute('DELETE FROM alerts WHERE hostname = ? AND metric_name = ?',
                       (hostname, metric_name))
        conn.commit()
        self.write({"status": "success"})


class AlertStateHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        cursor.execute('''
            UPDATE alerts
            SET enabled = ?
            WHERE hostname = ? AND metric_name = ?
        ''', (int(data['enabled']), data['hostname'], data['metric_name']))
        conn.commit()
        self.write({"status": "success"})


class DowntimeHandler(tornado.web.RequestHandler):
    def get(self):
        hostname = self.get_argument('hostname', None)
        query = 'SELECT id, hostname, start_time, end_time FROM downtimes'
        params = []
        if hostname and hostname != 'all':
            query += ' WHERE hostname = ?'
            params.append(hostname)
        query += ' ORDER BY start_time DESC'

        cursor.execute(query, params)
        downtimes = [
            {'id': row[0], 'hostname': row[1], 'start_time': row[2], 'end_time': row[3]}
            for row in cursor.fetchall()
        ]
        self.write(json.dumps(downtimes))

    def post(self):
        data = json.loads(self.request.body)
        cursor.execute('''
            INSERT INTO downtimes (hostname, start_time, end_time)
            VALUES (?, ?, ?)
        ''', (data['hostname'], data['start_time'], data['end_time']))
        conn.commit()
        self.write({"status": "success"})

    def delete(self):
        data = json.loads(self.request.body)
        cursor.execute('DELETE FROM downtimes WHERE id = ?', (data['id'],))
        conn.commit()
        self.write({"status": "success"})


class RecentAlertsHandler(tornado.web.RequestHandler):
    def get(self):
        hostname = self.get_argument('hostname', None)
        query = '''
            SELECT hostname, timestamp, additional_data
            FROM metrics
            WHERE metric_name = 'alert_triggered'
        '''
        params = []
        if hostname and hostname != 'all':
            query += ' AND hostname = ?'
            params.append(hostname)
        query += ' ORDER BY timestamp DESC LIMIT 10'

        cursor.execute(query, params)
        results = cursor.fetchall()
        recent_alerts = [{
            "hostname": row[0],
            "timestamp": row[1],
            **json.loads(row[2])
        } for row in results]
        self.write(json.dumps(recent_alerts))


class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        with open("dashboard.html", "r") as file:
            self.write(file.read())


class JSHandler(tornado.web.RequestHandler):
    def initialize(self, filename):
        self.filename = filename

    def get(self):
        with open(self.filename, "r") as file:
            self.set_header("Content-Type", "application/javascript")
            self.write(file.read())


class AggregationHandler(tornado.web.RequestHandler):
    def post(self):
        metrics_storage.aggregate_and_cleanup()
        self.write({"status": "Aggregation and cleanup completed"})


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/metrics", MetricsHandler),
        (r"/fetch/latest", FetchLatestHandler),
        (r"/fetch/history/([^/]+)/([^/]+)", FetchHistoryHandler),
        (r"/fetch/hosts", FetchHostsHandler),
        (r"/alert_config", AlertConfigHandler),
        (r"/alert_state", AlertStateHandler),
        (r"/downtime", DowntimeHandler),
        (r"/fetch/recent_alerts", RecentAlertsHandler),
        (r"/dashboard", DashboardHandler),
        (r"/dashboard.js", JSHandler, {"filename": "dashboard.js"}),
        (r"/chart.js", JSHandler, {"filename": "chart.js"}),
        (r"/alerts.js", JSHandler, {"filename": "alerts.js"}),
        (r"/downtimes.js", JSHandler, {"filename": "downtimes.js"}),
        (r"/utils.js", JSHandler, {"filename": "utils.js"}),
        (r"/aggregate", AggregationHandler),
    ])


def run_periodic_aggregation():
    metrics_storage.aggregate_and_cleanup()
    # Schedule the next aggregation after 24 hours
    tornado.ioloop.IOLoop.current().call_later(24 * 60 * 60, run_periodic_aggregation)


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Server started on http://localhost:8888")

    # Schedule the first aggregation after 1 hour
    tornado.ioloop.IOLoop.current().call_later(60 * 60, run_periodic_aggregation)

    tornado.ioloop.IOLoop.current().start()