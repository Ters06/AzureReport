from .routes import recs_bp
from .seeder import seed_recommendations

SERVICE_CONFIG = {
    'KEY': 'recommendations',
    'NAME': 'Recommendations',
    'BLUEPRINT': recs_bp,
    'MODEL_MODULES': ['.services.recommendations.models'],
    'SEEDER_FUNC': seed_recommendations,
    'CSV_FILE': None, 
    'SHOW_IN_NAV': False,
}