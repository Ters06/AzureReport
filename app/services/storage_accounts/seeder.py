import csv
import os
from .models import StorageAccount

STORAGE_ACCOUNTS_CSV = 'AzureStorageAccounts.csv'

def seed_storage_accounts(db, context):
    """Seeds storage account data from its CSV file."""
    if not os.path.exists(STORAGE_ACCOUNTS_CSV):
        print(f"Warning: {STORAGE_ACCOUNTS_CSV} not found. Skipping Storage Account seeding.")
        return

    storage_map = {}
    rg_map = context.get('rg_map', {})
    sub_map = context.get('sub_map', {})

    with open(STORAGE_ACCOUNTS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub_obj = sub_map.get(row['SUBSCRIPTION'].upper())
            if sub_obj:
                rg_obj = rg_map.get((row['RESOURCE GROUP'].upper(), sub_obj.id))
                if rg_obj:
                    sa = StorageAccount(
                        name=row['NAME'], 
                        location=row['LOCATION'], 
                        sku=row['TYPE'], 
                        kind=row['KIND'], 
                        resource_group=rg_obj
                    )
                    db.session.add(sa)
                    storage_map[sa.name.upper()] = sa
    db.session.commit()
    print(f"Seeded {len(storage_map)} Storage Accounts.")
    context['storage_map'] = storage_map
