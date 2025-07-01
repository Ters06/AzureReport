import csv
import os
from .models import VMSS

def seed_vmss(db, context):
    """Seeds VM Scale Set data from its CSV file."""
    VMSS_CSV = 'AzurevirtualMachineScaleSets.csv'
    if not os.path.exists(VMSS_CSV):
        print(f"Warning: {VMSS_CSV} not found. Skipping VMSS seeding.")
        return

    vmss_map = {}
    rg_map = context.get('rg_map', {})
    sub_map = context.get('sub_map', {})

    with open(VMSS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub_obj = sub_map.get(row['SUBSCRIPTION'].upper())
            if sub_obj:
                # FIX: Use lowercase for lookup key
                rg_id_key = f"/subscriptions/{sub_obj.id}/resourceGroups/{row['RESOURCE GROUP']}".lower()
                rg_obj = rg_map.get(rg_id_key)
                if rg_obj:
                    # FIX: Create resource ID in lowercase
                    vmss_id = f"{rg_obj.id}/providers/microsoft.compute/virtualmachinescalesets/{row['NAME']}".lower()
                    vmss = VMSS(
                        id=vmss_id, name=row['NAME'], type='Virtual machine scale set', location=row['LOCATION'],
                        resource_group_id=rg_obj.id, status=row['STATUS'], os=row['OPERATING SYSTEM'], 
                        size=row['SIZE'], instances=row['INSTANCES']
                    )
                    db.session.add(vmss)
                    vmss_map[vmss_id] = vmss

    db.session.commit()
    print(f"Seeded {len(vmss_map)} VM Scale Sets.")
    context['vmss_map'] = vmss_map
