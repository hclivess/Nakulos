import bcrypt
import tornado.web
from database import get_db
import logging

logger = logging.getLogger(__name__)

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.db = get_db()

    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if user_id:
            return user_id
        return None

class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("login.html")

    async def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")

        user = await self.check_credentials(username, password)
        if user:
            self.set_secure_cookie("user", str(user['id']))
            logger.info(f"User {username} logged in successfully")
            self.redirect("/dashboard")
        else:
            logger.warning(f"Failed login attempt for user {username}")
            self.render("login.html", error="Invalid username or password")

    async def check_credentials(self, username, password):
        db = get_db()
        try:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()

                if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                    return user
        except Exception as e:
            logger.error(f"Database error during login: {e}")
        return None

class RegisterHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("register.html")

    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        confirm_password = self.get_argument("confirm_password", "")

        if password != confirm_password:
            self.write("Passwords do not match")
            return

        if self.username_exists(username):
            self.write("Username already exists")
            return

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        db = get_db()
        with db.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed_password.decode('utf-8'))
            )

        self.redirect("/login")

    def username_exists(self, username):
        db = get_db()
        with db.get_cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            return cursor.fetchone() is not None

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/login")