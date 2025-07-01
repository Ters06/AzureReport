import csv
import os
from .models import ClientInfo, Subscription, ResourceGroup

def seed_core_data(db, context):
    """Seeds ClientInfo, Subscriptions, and Resource Groups."""
    client_name = context.get('client_name')
    report_date = context.get('report_date')
    if client_name and report_date:
        client_info = ClientInfo(name=client_name, report_date=report_date)
        db.session.add(client_info)
    
    sub_map = {}
    if os.path.exists('Subscriptions.csv'):
        with open('Subscriptions.csv', 'r', encoding='utf-8-sig') as f:
            if 'sep=' in f.readline().lower(): pass
            else: f.seek(0)
            reader = csv.DictReader(f)
            for row in reader:
                sub_id = row['SUBSCRIPTION ID']
                sub = Subscription(id=sub_id, name=row['SUBSCRIPTION NAME'])
                db.session.add(sub)
                sub_map[sub.name.upper()] = sub
        db.session.commit()
        print(f"Seeded {len(sub_map)} subscriptions.")
    else:
        print("Warning: Subscriptions.csv not found.")
    
    rg_map = {}
    if os.path.exists('Azureresourcegroups.csv'):
        with open('Azureresourcegroups.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sub_obj = sub_map.get(row['SUBSCRIPTION'].upper())
                if sub_obj:
                    # FIX: Store all generated IDs and map keys in lowercase
                    rg_id = f"/subscriptions/{sub_obj.id}/resourceGroups/{row['NAME']}".lower()
                    rg = ResourceGroup(id=rg_id, name=row['NAME'], subscription_id=sub_obj.id)
                    db.session.add(rg)
                    rg_map[rg_id] = rg
        db.session.commit()
        print(f"Seeded {len(rg_map)} resource groups.")
    else:
        print("Warning: Azureresourcegroups.csv not found.")

    context['sub_map'] = sub_map
    context['rg_map'] = rg_map
