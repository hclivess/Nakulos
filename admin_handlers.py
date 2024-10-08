import json
import logging
from auth_handlers import BaseHandler

logger = logging.getLogger(__name__)

class FetchClientIdsHandler(BaseHandler):
    async def get(self):
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT client_id FROM client_configs")
                client_ids = [row['client_id'] for row in cursor.fetchall()]
            self.write(json.dumps(client_ids))
        except Exception as e:
            logger.error(f"Error in FetchClientIdsHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class AdminInterfaceHandler(BaseHandler):
    def get(self):
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT hostname FROM hosts")
                hosts = [row['hostname'] for row in cursor.fetchall()]
            self.render("admin_interface.html", hosts=hosts)
        except Exception as e:
            logger.error(f"Error in AdminInterfaceHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class UpdateClientHandler(BaseHandler):
    def post(self):
        data = json.loads(self.request.body)
        client_id = data.get('client_id')
        hostname = data.get('hostname')
        config = data.get('config')

        if not client_id or not hostname or not config:
            self.set_status(400)
            self.write({"message": "client_id, hostname, and config are required"})
            return

        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO client_configs (client_id, hostname, config)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (client_id) DO UPDATE
                    SET hostname = EXCLUDED.hostname, config = EXCLUDED.config, last_updated = NOW()
                """, (client_id, hostname, json.dumps(config)))
            self.write({"message": "Client configuration updated successfully"})
        except Exception as e:
            logger.error(f"Error updating client configuration: {str(e)}")
            self.set_status(500)
            self.write({"message": "Internal server error"})


class UploadMetricHandler(BaseHandler):
    def post(self):
        data = json.loads(self.request.body)
        metric_name = data.get('name')
        metric_code = data.get('code')
        tags = data.get('tags', [])

        if not metric_name or not metric_code:
            self.set_status(400)
            self.write({"message": "Both name and code are required"})
            return

        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO metric_scripts (name, code, tags)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name) DO UPDATE
                    SET code = EXCLUDED.code, tags = EXCLUDED.tags
                """, (metric_name, metric_code, json.dumps(tags)))

            self.write({"message": f"Metric '{metric_name}' uploaded successfully"})
        except Exception as e:
            logger.error(f"Error uploading metric: {str(e)}")
            self.set_status(500)
            self.write({"message": "Internal server error"})