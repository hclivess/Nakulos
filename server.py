import tornado.ioloop
import tornado.web
from tornado.options import define, options
import json
from routes import make_app
from database import init_db, get_db
from queue_manager import MetricProcessor

define("port", default=8888, help="run on the given port", type=int)


def load_config():
    with open('server_config.json', 'r') as config_file:
        return json.load(config_file)


config = load_config()


def main():
    tornado.options.parse_command_line()
    init_db(config['database'])
    db = get_db()
    metric_processor = MetricProcessor()
    metric_processor.start()

    app = make_app(metric_processor)
    app.listen(options.port)
    print(f"Server started on http://localhost:{options.port}")

    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        metric_processor.stop()
        db.close()


if __name__ == "__main__":
    main()