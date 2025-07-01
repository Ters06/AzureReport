from .routes import storage_bp
from .seeder import seed_storage_accounts

SERVICE_CONFIG = {
    'KEY': 'storage_accounts',
    'NAME': 'Storage Accounts',
    'BLUEPRINT': storage_bp,
    'MODEL_MODULES': ['.services.storage_accounts.models'],
    # FIX: Add the correct model class name
    'MODEL_CLASS_NAME': 'StorageAccount',
    'SEEDER_FUNC': seed_storage_accounts,
    'CSV_FILE': 'AzureStorageAccounts.csv',
    'SHOW_IN_NAV': True,
    'NAV_ORDER': 3,
    'LIST_ROUTE': 'storage.storage_accounts_list',
    'DETAIL_ROUTE': 'storage.storage_account_detail'
}