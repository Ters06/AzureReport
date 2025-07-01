import os
import importlib
from flask import Flask
from .db import db # Import db from the new central file

def get_service_configs():
    """
    Dynamically discovers and imports service configurations.
    """
    configs = []
    services_dir = os.path.join(os.path.dirname(__file__), 'services')
    for service_name in os.listdir(services_dir):
        service_path = os.path.join(services_dir, service_name)
        if os.path.isdir(service_path) and '__init__.py' in os.listdir(service_path):
            try:
                module = importlib.import_module(f'.services.{service_name}', package='app')
                if hasattr(module, 'SERVICE_CONFIG'):
                    configs.append(getattr(module, 'SERVICE_CONFIG'))
            except ImportError as e:
                print(f"Could not import service {service_name}: {e}")
    return configs

def create_app():
    """Application factory function."""
    app = Flask(__name__, instance_relative_config=True)

    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(basedir, 'report.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    app.service_configs = get_service_configs()

    # Load all service models so SQLAlchemy knows about them
    for config in app.service_configs:
        if 'MODEL_MODULES' in config:
            for model_module in config['MODEL_MODULES']:
                 importlib.import_module(model_module, package='app')

    # Initialize extensions
    db.init_app(app)

    # Register all blueprints within the app context
    with app.app_context():
        from .routes import main, api
        app.register_blueprint(main.main_bp)
        app.register_blueprint(api.api_bp, url_prefix='/api')
        
        for config in app.service_configs:
            if 'BLUEPRINT' in config:
                app.register_blueprint(config['BLUEPRINT'])

        from . import context_processors
        app.context_processor(context_processors.inject_global_vars)
        app.template_filter('format_currency')(context_processors.format_currency)

    return app
