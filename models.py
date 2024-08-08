class Host:
    def __init__(self, id=None, hostname=None, alias=None, location=None):
        self.id = id
        self.hostname = hostname
        self.alias = alias
        self.location = location

class Metric:
    def __init__(self, id=None, host_id=None, metric_name=None, timestamp=None, value=None):
        self.id = id
        self.host_id = host_id
        self.metric_name = metric_name
        self.timestamp = timestamp
        self.value = value

class Alert:
    def __init__(self, id=None, host_id=None, metric_name=None, condition=None, threshold=None, duration=None, enabled=True):
        self.id = id
        self.host_id = host_id
        self.metric_name = metric_name
        self.condition = condition
        self.threshold = threshold
        self.duration = duration
        self.enabled = enabled