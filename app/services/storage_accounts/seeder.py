import csv
import os
from .models import StorageAccount

def seed_storage_accounts(db, context):
    """Seeds storage account data from its CSV file."""
    STORAGE_ACCOUNTS_CSV = 'AzureStorageAccounts.csv'
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
                # FIX: Use lowercase for lookup key
                rg_id_key = f"/subscriptions/{sub_obj.id}/resourceGroups/{row['RESOURCE GROUP']}".lower()
                rg_obj = rg_map.get(rg_id_key)
                if rg_obj:
                    # FIX: Create resource ID in lowercase
                    sa_id = f"{rg_obj.id}/providers/microsoft.storage/storageaccounts/{row['NAME']}".lower()
                    sa = StorageAccount(
                        id=sa_id, name=row['NAME'], type='Storage account', location=row['LOCATION'],
                        resource_group_id=rg_obj.id, sku=row['TYPE'], kind=row['KIND']
                    )
                    db.session.add(sa)
                    storage_map[sa_id] = sa

    db.session.commit()
    print(f"Seeded {len(storage_map)} Storage Accounts.")
    context['storage_map'] = storage_map
