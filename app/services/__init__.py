import os
import importlib

def get_service_configs():
    """
    Dynamically discovers and imports service configurations from all subdirectories.
    """
    configs = []
    services_dir = os.path.dirname(__file__)
    for service_name in os.listdir(services_dir):
        service_path = os.path.join(services_dir, service_name)
        if os.path.isdir(service_path) and '__init__.py' in os.listdir(service_path):
            try:
                module = importlib.import_module(f'.{service_name}', package='app.services')
                if hasattr(module, 'SERVICE_CONFIG'):
                    configs.append(getattr(module, 'SERVICE_CONFIG'))
            except ImportError as e:
                print(f"Could not import service {service_name}: {e}")
    return configs
