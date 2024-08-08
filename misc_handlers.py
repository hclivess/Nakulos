import tornado.web
import logging
from auth_handlers import BaseHandler
from data_aggregator import aggregate_data

logger = logging.getLogger(__name__)

class MainHandler(BaseHandler):
    def get(self):
        self.write("Monitoring Server is running")

class JSHandler(BaseHandler):
    def initialize(self, filename):
        super().initialize()
        self.filename = filename

    def get(self):
        try:
            with open(self.filename, "r") as file:
                self.set_header("Content-Type", "application/javascript")
                self.write(file.read())
        except Exception as e:
            logger.error(f"Error in JSHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class AggregateDataHandler(BaseHandler):
    def get(self):
        try:
            aggregate_data()
            self.write({"status": "Data aggregation triggered successfully"})
        except Exception as e:
            logger.error(f"Error in AggregateDataHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})