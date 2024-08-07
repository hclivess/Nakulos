import tornado.web
from auth_handlers import LoginHandler, RegisterHandler, LogoutHandler
from metric_handlers import (MetricsHandler, FetchLatestHandler, FetchHistoryHandler,
                             FetchMetricsForHostHandler, DeleteMetricsHandler)
from host_handlers import FetchHostsHandler, RemoveHostHandler, UpdateTagsHandler
from alert_handlers import AlertConfigHandler, AlertStateHandler, RecentAlertsHandler
from downtime_handlers import DowntimeHandler
from admin_handlers import AdminInterfaceHandler, UpdateClientHandler, UploadMetricHandler
from dashboard_handlers import DashboardHandler
from client_handlers import ClientConfigHandler, FetchMetricsHandler
from misc_handlers import MainHandler, JSHandler, AggregateDataHandler

def make_app(metric_processor, config):
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/login", LoginHandler),
        (r"/register", RegisterHandler),
        (r"/logout", LogoutHandler),
        (r"/fetch/metrics_for_host", FetchMetricsForHostHandler),
        (r"/fetch_metrics", FetchMetricsHandler),
        (r"/update_tags", UpdateTagsHandler),
        (r"/admin", AdminInterfaceHandler),
        (r"/admin/update_client", UpdateClientHandler),
        (r"/admin/upload_metric", UploadMetricHandler),
        (r"/client_config", ClientConfigHandler),
        (r"/metrics", MetricsHandler, dict(metric_processor=metric_processor, secret_key=config['metrics']['secret_key'])),
        (r"/fetch/latest", FetchLatestHandler),
        (r"/fetch/history/([^/]+)/([^/]+)", FetchHistoryHandler),
        (r"/fetch/hosts", FetchHostsHandler),
        (r"/alert_config", AlertConfigHandler),
        (r"/alert_state", AlertStateHandler),
        (r"/downtime", DowntimeHandler),
        (r"/fetch/recent_alerts", RecentAlertsHandler),
        (r"/dashboard", DashboardHandler),
        (r"/dashboard.js", JSHandler, {"filename": "dashboard.js"}),
        (r"/delete_metrics", DeleteMetricsHandler),
        (r"/chart.js", JSHandler, {"filename": "chart.js"}),
        (r"/alerts.js", JSHandler, {"filename": "alerts.js"}),
        (r"/admin.js", JSHandler, {"filename": "admin.js"}),
        (r"/downtimes.js", JSHandler, {"filename": "downtimes.js"}),
        (r"/utils.js", JSHandler, {"filename": "utils.js"}),
        (r"/aggregate", AggregateDataHandler),
        (r"/remove_host", RemoveHostHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"})
    ],
    cookie_secret=config["webapp"]["cookie_secret"],
    login_url="/login"
    )