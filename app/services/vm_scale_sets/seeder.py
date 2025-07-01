import csv
import os
from .models import VMSS

VMSS_CSV = 'AzurevirtualMachineScaleSets.csv'

def seed_vmss(db, context):
    """Seeds VM Scale Set data from its CSV file."""
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
                rg_obj = rg_map.get((row['RESOURCE GROUP'].upper(), sub_obj.id))
                if rg_obj:
                    vmss = VMSS(
                        name=row['NAME'], 
                        location=row['LOCATION'], 
                        provisioning_state=row['PROVISIONING STATE'],
                        status=row['STATUS'], 
                        os=row['OPERATING SYSTEM'], 
                        size=row['SIZE'], 
                        instances=row['INSTANCES'], 
                        orchestration_mode=row['ORCHESTRATION MODE'],
                        public_ip=row['PUBLIC IP ADDRESS'], 
                        resource_group=rg_obj
                    )
                    db.session.add(vmss)
                    vmss_map[vmss.name.upper()] = vmss
    db.session.commit()
    print(f"Seeded {len(vmss_map)} VM Scale Sets.")
    context['vmss_map'] = vmss_map
