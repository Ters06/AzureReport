from .seeder import seed_core_data

SERVICE_CONFIG = {
    'KEY': 'core',
    'NAME': 'Core Components',
    # FIX: Corrected model module path
    'MODEL_MODULES': ['.services.core.models'],
    'SEEDER_FUNC': seed_core_data,
}