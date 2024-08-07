import json
import logging
from auth_handlers import BaseHandler

logger = logging.getLogger(__name__)

class DashboardHandler(BaseHandler):
    def get(self):
        try:
            host = self.get_argument('host', None)

            with open("dashboard.html", "r") as file:
                dashboard_html = file.read()

            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT hostname, tags FROM hosts")
                hosts = {row['hostname']: {'tags': row['tags']} for row in cursor.fetchall()}

            selected_host = None
            if host and host in hosts:
                selected_host = host
            elif host:
                logger.warning(f"Requested host '{host}' not found")

            template_data = {
                "hosts": json.dumps(hosts),
                "selected_host": json.dumps(selected_host)
            }

            for key, value in template_data.items():
                placeholder = f"{{{{ {key} }}}}"
                dashboard_html = dashboard_html.replace(placeholder, value)

            self.write(dashboard_html)

        except Exception as e:
            logger.error(f"Error in DashboardHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

    def post(self):
        self.set_status(405)
        self.write({"error": "POST method not supported for dashboard"})