import os
from flask import Flask
from .models import db

def create_app():
    """Application factory function."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(basedir, 'report.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # --- Extensions ---
    db.init_app(app)

    # --- Application Context ---
    with app.app_context():
        # --- Blueprints ---
        from .routes import main, vms, recommendations, api
        app.register_blueprint(main.main_bp)
        app.register_blueprint(vms.vms_bp)
        app.register_blueprint(recommendations.recs_bp)
        
        # FIX: Register the API blueprint with the correct URL prefix
        app.register_blueprint(api.api_bp, url_prefix='/api')

        # --- Context Processors and Template Filters ---
        from . import context_processors
        app.context_processor(context_processors.inject_global_vars)
        app.template_filter('format_currency')(context_processors.format_currency)

        return app
