import importlib.util
import os
import time
import logging

logger = logging.getLogger(__name__)

class MetricCollector:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.metrics_modules = {}
        self.last_collection_times = {}
        self.load_metric_modules()

    def load_metric_modules(self):
        for filename in os.listdir(self.config_manager.metrics_dir):
            if filename.endswith('.py'):
                module_name = filename[:-3]
                module_path = os.path.join(self.config_manager.metrics_dir, filename)
                try:
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, 'collect'):
                        self.metrics_modules[module_name] = module
                        logger.info(f"Loaded metric module: {module_name}")
                    else:
                        logger.warning(f"Metric module {module_name} does not have a 'collect' function")
                except Exception as e:
                    logger.error(f"Error loading metric module {module_name}: {str(e)}")

    def get_metric_interval(self, metric_name):
        return self.config_manager.metric_intervals.get(metric_name, self.config_manager.default_interval)

    def collect_metrics(self):
        current_time = time.time()
        collected_metrics = {}
        for name, module in self.metrics_modules.items():
            interval = self.get_metric_interval(name)
            last_collection = self.last_collection_times.get(name, 0)
            if current_time - last_collection >= interval:
                try:
                    value = module.collect()
                    collected_metrics[name] = {'value': value, 'timestamp': current_time}
                    self.last_collection_times[name] = current_time
                    logger.info(f"Collected metric {name}: {value}")
                except Exception as e:
                    logger.error(f"Error collecting metric {name}: {e}", exc_info=True)
        return collected_metrics

    def get_shortest_interval(self):
        if not self.metrics_modules:
            return self.config_manager.default_interval
        return min(self.get_metric_interval(metric) for metric in self.metrics_modules.keys())

    def update_metric_script(self, metric_name, metric_code):
        file_path = os.path.join(self.config_manager.metrics_dir, f"{metric_name}.py")
        try:
            with open(file_path, 'w') as f:
                f.write(metric_code)
            logger.info(f"Updated metric script: {metric_name}")
            self.reload_metric_module(metric_name)
        except Exception as e:
            logger.error(f"Error updating metric script {metric_name}: {str(e)}")

    def reload_metric_module(self, metric_name):
        file_path = os.path.join(self.config_manager.metrics_dir, f"{metric_name}.py")
        try:
            spec = importlib.util.spec_from_file_location(metric_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'collect'):
                self.metrics_modules[metric_name] = module
                logger.info(f"Reloaded metric module: {metric_name}")
            else:
                logger.warning(f"Reloaded metric module {metric_name} does not have a 'collect' function")
        except Exception as e:
            logger.error(f"Error reloading metric module {metric_name}: {str(e)}")

    def remove_metric_script(self, metric_name):
        file_path = os.path.join(self.config_manager.metrics_dir, f"{metric_name}.py")
        try:
            os.remove(file_path)
            self.metrics_modules.pop(metric_name, None)
            self.last_collection_times.pop(metric_name, None)
            logger.info(f"Removed metric script: {metric_name}")
        except Exception as e:
            logger.error(f"Error removing metric script {metric_name}: {str(e)}")

    def list_available_metrics(self):
        return list(self.metrics_modules.keys())

    def get_metric_info(self, metric_name):
        if metric_name in self.metrics_modules:
            module = self.metrics_modules[metric_name]
            return {
                "name": metric_name,
                "interval": self.get_metric_interval(metric_name),
                "last_collection": self.last_collection_times.get(metric_name, 0),
                "description": getattr(module, 'description', 'No description available')
            }
        return None