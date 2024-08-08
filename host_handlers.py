import logging
import json
import traceback
from auth_handlers import BaseHandler

logger = logging.getLogger(__name__)

class FetchHostsHandler(BaseHandler):
    async def get(self):
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT hostname, tags FROM hosts")
                hosts = cursor.fetchall()

            result = {}
            for host in hosts:
                hostname = host['hostname']
                tags = host['tags'] if isinstance(host['tags'], dict) else {}
                result[hostname] = {"tags": tags}

            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(result))
        except Exception as e:
            logger.error(f"Error in FetchHostsHandler: {str(e)}")
            self.set_status(500)
            self.write(json.dumps({"error": "Internal server error"}))

class RemoveHostHandler(BaseHandler):
    async def post(self):
        try:
            data = json.loads(self.request.body)
            hostname = data.get('hostname')

            if not hostname:
                self.set_status(400)
                self.write(json.dumps({"error": "Hostname is required"}))
                return

            with self.db.get_cursor() as cursor:
                cursor.execute("BEGIN")
                try:
                    cursor.execute("DELETE FROM hosts WHERE hostname = %s", (hostname,))
                    if cursor.rowcount == 0:
                        cursor.execute("ROLLBACK")
                        self.set_status(404)
                        self.write(json.dumps({"error": "Host not found"}))
                    else:
                        cursor.execute("COMMIT")
                        self.write(json.dumps({"status": "success", "message": f"Host {hostname} removed successfully"}))
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    raise e

        except Exception as e:
            logger.error(f"Error in RemoveHostHandler: {str(e)}")
            self.set_status(500)
            self.write(json.dumps({"error": "Internal server error"}))

class UpdateTagsHandler(BaseHandler):
    async def post(self):
        try:
            data = json.loads(self.request.body)
            hostname = data.get('hostname')
            new_tags = data.get('tags')

            logger.info(f"Received update tags request for hostname: {hostname}, new tags: {new_tags}")

            if not hostname or new_tags is None:
                self.set_status(400)
                self.write({"error": "Both hostname and tags are required"})
                return

            with self.db.get_cursor() as cursor:
                # First, get the current client configuration
                cursor.execute("""
                    SELECT client_id, config
                    FROM client_configs
                    WHERE hostname = %s
                """, (hostname,))
                result = cursor.fetchone()

                if not result:
                    self.set_status(404)
                    self.write({"error": f"Host not found: {hostname}"})
                    return

                client_id, current_config = result['client_id'], result['config']

                # If current_config is a string, parse it to a dictionary
                if isinstance(current_config, str):
                    current_config = json.loads(current_config)
                elif not isinstance(current_config, dict):
                    current_config = {}

                logger.info(f"Current config for {hostname}: {current_config}")

                # Merge new tags with existing tags
                current_tags = current_config.get('tags', {})
                current_tags.update(new_tags)
                current_config['tags'] = current_tags

                logger.info(f"Updated config for {hostname}: {current_config}")

                # Convert the updated config back to a JSON string
                updated_config_json = json.dumps(current_config)

                # Update the client configuration with the merged tags
                cursor.execute("""
                    UPDATE client_configs
                    SET config = %s, last_updated = NOW()
                    WHERE client_id = %s
                """, (updated_config_json, client_id))

            self.write({"message": f"Client configuration updated with merged tags for {hostname}. Client will fetch on next check."})
        except Exception as e:
            logger.error(f"Error updating client configuration with merged tags: {str(e)}")
            logger.error(traceback.format_exc())
            self.set_status(500)
            self.write({"error": f"Internal server error: {str(e)}"})