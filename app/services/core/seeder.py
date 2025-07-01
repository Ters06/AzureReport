import csv

from .models import Subscription, ResourceGroup

SUBSCRIPTIONS_CSV = 'Subscriptions.csv'
RESOURCE_GROUPS_CSV = 'Azureresourcegroups.csv'

def seed_core_data(db, context):
    """Seeds subscriptions and resource groups."""
    # --- Subscriptions ---
    sub_name_map = {}
    with open(SUBSCRIPTIONS_CSV, 'r', encoding='utf-8-sig') as f:
        if 'sep=' in f.readline().lower(): pass
        else: f.seek(0)
        reader = csv.DictReader(f)
        for row in reader:
            sub = Subscription(name=row['SUBSCRIPTION NAME'], subscription_id_guid=row['SUBSCRIPTION ID'])
            db.session.add(sub)
            sub_name_map[sub.name.upper()] = sub
    db.session.commit()
    print(f"Seeded {len(sub_name_map)} subscriptions.")
    
    # --- Resource Groups ---
    rg_map = {}
    with open(RESOURCE_GROUPS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub_obj = sub_name_map.get(row['SUBSCRIPTION'].upper())
            if sub_obj:
                rg = ResourceGroup(name=row['NAME'], subscription=sub_obj)
                db.session.add(rg)
                rg_map[(rg.name.upper(), sub_obj.id)] = rg
    db.session.commit()
    print(f"Seeded {len(rg_map)} resource groups.")

    # Pass the created maps to the context for other seeders to use
    context['sub_map'] = sub_name_map
    context['rg_map'] = rg_map
