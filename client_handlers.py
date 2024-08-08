import json
import logging
from auth_handlers import BaseHandler

logger = logging.getLogger(__name__)

import json
import logging
from auth_handlers import BaseHandler

logger = logging.getLogger(__name__)


class ClientConfigHandler(BaseHandler):
    async def get(self):
        client_id = self.get_argument('client_id', None)
        if not client_id:
            self.set_status(400)
            self.write({"error": "Client ID is required"})
            return

        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT config, last_updated FROM client_configs WHERE client_id = %s", (client_id,))
                result = cursor.fetchone()

            if result:
                config, last_updated = result['config'], result['last_updated']
                client_last_update = self.get_argument('last_update', '0')
                logger.info(f"Client last update: {client_last_update}, Server last updated: {last_updated}")
                if str(last_updated.timestamp()) > client_last_update:
                    self.write({
                        "status": "update_available",
                        "config": config
                    })
                else:
                    self.write({"status": "no_update"})
            else:
                self.set_status(404)
                self.write({"status": "unknown_client"})
        except Exception as e:
            logger.error(f"Error in ClientConfigHandler GET: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

    async def post(self):
        data = json.loads(self.request.body)
        client_id = data.get('client_id')
        hostname = data.get('hostname')
        new_config = data.get('config')
        new_tags = data.get('tags', {})

        if not client_id or not hostname or not new_config:
            self.set_status(400)
            self.write({"error": "client_id, hostname, and config are required"})
            return

        try:
            with self.db.get_cursor() as cursor:
                # First, get the current config
                cursor.execute("SELECT config FROM client_configs WHERE client_id = %s", (client_id,))
                result = cursor.fetchone()

                if result:
                    current_config = json.loads(result['config'])

                    # Merge new config with current config
                    self.merge_configs(current_config, new_config)

                    # Merge new tags with current tags
                    current_tags = current_config.get('tags', {})
                    current_tags.update(new_tags)
                    current_config['tags'] = current_tags

                    updated_config_json = json.dumps(current_config)

                    if updated_config_json == result['config']:
                        self.write({"status": "success", "message": "No changes to config"})
                    else:
                        cursor.execute("""
                            UPDATE client_configs
                            SET hostname = %s, config = %s, last_updated = NOW()
                            WHERE client_id = %s
                        """, (hostname, updated_config_json, client_id))
                        self.write({"status": "success", "message": "Client config updated successfully"})
                else:
                    # New client, insert the config as is
                    cursor.execute("""
                        INSERT INTO client_configs (client_id, hostname, config, last_updated)
                        VALUES (%s, %s, %s, NOW())
                    """, (client_id, hostname, json.dumps(new_config)))
                    self.write({"status": "success", "message": "New client config created successfully"})
        except Exception as e:
            logger.error(f"Error in ClientConfigHandler POST: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

    def merge_configs(self, current_config, new_config):
        for key, value in new_config.items():
            if isinstance(value, dict) and key in current_config and isinstance(current_config[key], dict):
                self.merge_configs(current_config[key], value)
            else:
                current_config[key] = value

class FetchMetricsHandler(BaseHandler):
    async def get(self):
        client_id = self.get_argument('client_id', None)
        if not client_id:
            self.set_status(400)
            self.write({"error": "Client ID is required"})
            return

        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT tags FROM client_configs WHERE client_id = %s", (client_id,))
                result = cursor.fetchone()
                if not result:
                    self.set_status(404)
                    self.write({"error": "Client not found"})
                    return

                client_tags = result['tags'] or {}

                cursor.execute("""
                    SELECT name, code
                    FROM metric_scripts
                    WHERE tags @> %s OR tags IS NULL OR tags = '{}' OR %s = '{}'
                """, (json.dumps(client_tags), json.dumps(client_tags)))

                metrics = {row['name']: row['code'] for row in cursor.fetchall()}

            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(metrics))
        except Exception as e:
            logger.error(f"Error in FetchMetricsHandler: {str(e)}")
            self.set_status(500)
            self.set_header("Content-Type", "application/json")
            self.write({"error": "Internal server error"})