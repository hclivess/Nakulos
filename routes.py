import tornado.web
from handlers import (MainHandler, MetricsHandler, FetchLatestHandler,
                      FetchHistoryHandler, FetchHostsHandler, AlertConfigHandler,
                      AlertStateHandler, DowntimeHandler, RecentAlertsHandler,
                      DashboardHandler, JSHandler, AggregateDataHandler)

def make_app(metric_processor):
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/metrics", MetricsHandler, dict(metric_processor=metric_processor)),
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
        (r"/aggregate", AggregateDataHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"}),
    ])