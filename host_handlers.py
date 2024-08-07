import json
import logging
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
        data = json.loads(self.request.body)
        hostname = data.get('hostname')
        new_tags = data.get('tags')

        if not hostname or new_tags is None:
            self.set_status(400)
            self.write({"error": "Both hostname and tags are required"})
            return

        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE hosts
                    SET tags = %s
                    WHERE hostname = %s
                """, (json.dumps(new_tags), hostname))

                if cursor.rowcount == 0:
                    self.set_status(404)
                    self.write({"error": "Host not found"})
                else:
                    self.write({"message": "Tags updated successfully"})
        except Exception as e:
            logger.error(f"Error updating tags: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})