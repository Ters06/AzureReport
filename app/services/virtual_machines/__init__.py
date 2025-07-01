from .routes import vms_bp
from .seeder import seed_vms

SERVICE_CONFIG = {
    'KEY': 'virtual_machines',
    'NAME': 'Virtual Machines',
    'BLUEPRINT': vms_bp,
    'MODEL_MODULES': ['.services.virtual_machines.models'],
    # FIX: Add the correct model class name
    'MODEL_CLASS_NAME': 'VM',
    'SEEDER_FUNC': seed_vms,
    'CSV_FILE': 'AzureVirtualMachines.csv',
    'SHOW_IN_NAV': True,
    'NAV_ORDER': 1,
    'LIST_ROUTE': 'vms.vms_list',
    'DETAIL_ROUTE': 'vms.vm_detail'
}