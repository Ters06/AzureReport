from .routes import vmss_bp
from .seeder import seed_vmss

SERVICE_CONFIG = {
    'KEY': 'vm_scale_sets',
    'NAME': 'VM Scale Sets',
    'BLUEPRINT': vmss_bp,
    'MODEL_MODULES': ['.services.vm_scale_sets.models'],
    # FIX: Add the correct model class name
    'MODEL_CLASS_NAME': 'VMSS',
    'SEEDER_FUNC': seed_vmss,
    'CSV_FILE': 'AzurevirtualMachineScaleSets.csv',
    'SHOW_IN_NAV': True,
    'NAV_ORDER': 2,
    'LIST_ROUTE': 'vmss.vmss_list',
    'DETAIL_ROUTE': 'vmss.vmss_detail'
}