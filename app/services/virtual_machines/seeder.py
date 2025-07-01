import csv
import os
from .models import VM

def seed_vms(db, context):
    """Seeds virtual machine data from its CSV file."""
    VMS_CSV = 'AzureVirtualMachines.csv'
    if not os.path.exists(VMS_CSV):
        print(f"Warning: {VMS_CSV} not found. Skipping VM seeding.")
        return

    vm_map = {}
    rg_map = context.get('rg_map', {})
    sub_map = context.get('sub_map', {})

    with open(VMS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub_obj = sub_map.get(row['SUBSCRIPTION'].upper())
            if sub_obj:
                # FIX: Use lowercase for lookup key
                rg_id_key = f"/subscriptions/{sub_obj.id}/resourceGroups/{row['RESOURCE GROUP']}".lower()
                rg_obj = rg_map.get(rg_id_key)
                if rg_obj:
                    # FIX: Create resource ID in lowercase
                    vm_id = f"{rg_obj.id}/providers/microsoft.compute/virtualmachines/{row['NAME']}".lower()
                    vm = VM(
                        id=vm_id, name=row['NAME'], type='Virtual machine', location=row['LOCATION'],
                        resource_group_id=rg_obj.id, status=row['STATUS'], os=row['OPERATING SYSTEM'], 
                        size=row['SIZE'], public_ip=row['PUBLIC IP ADDRESS'], disks=row['DISKS']
                    )
                    db.session.add(vm)
                    vm_map[vm_id] = vm
    
    db.session.commit()
    print(f"Seeded {len(vm_map)} VMs.")
    context['vm_map'] = vm_map
