import csv
import os
from .models import VM

VMS_CSV = 'AzureVirtualMachines.csv'

def seed_vms(db, context):
    """Seeds virtual machine data from its CSV file."""
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
                rg_obj = rg_map.get((row['RESOURCE GROUP'].upper(), sub_obj.id))
                if rg_obj:
                    vm = VM(
                        name=row['NAME'], 
                        location=row['LOCATION'], 
                        status=row['STATUS'], 
                        os=row['OPERATING SYSTEM'], 
                        size=row['SIZE'], 
                        public_ip=row['PUBLIC IP ADDRESS'], 
                        disks=row['DISKS'], 
                        resource_group=rg_obj
                    )
                    db.session.add(vm)
                    vm_map[vm.name.upper()] = vm
    db.session.commit()
    print(f"Seeded {len(vm_map)} VMs.")
    context['vm_map'] = vm_map
