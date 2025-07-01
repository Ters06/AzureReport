import os
import csv
import glob
import re
import argparse
from datetime import datetime

# Import the application factory and db instance from the app package
from app import create_app, db
# Import models directly from the app package's models module
from app.models import ClientInfo, Subscription, ResourceGroup, VM, VMSS, RecommendationType, RecommendationInstance

# --- Configuration ---
VMS_CSV = 'AzureVirtualMachines.csv'
VMSS_CSV = 'AzurevirtualMachineScaleSets.csv'
SUBSCRIPTIONS_CSV = 'Subscriptions.csv'
RESOURCE_GROUPS_CSV = 'Azureresourcegroups.csv'

def find_advisor_file():
    """Finds the advisor CSV file and extracts the date from its name."""
    files = glob.glob('Advisor*.csv')
    if not files:
        print("Error: No Advisor CSV file found (e.g., 'Advisor_....csv'). Please add one to the root directory.")
        exit(1)
    
    filename = files[0]
    print(f"Found Advisor file: {filename}")
    
    match = re.search(r'_(\d{4}-\d{2}-\d{2})T', filename)
    if match:
        date_str = match.group(1)
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')
            print(f"Extracted report date: {report_date}")
            return filename, report_date
        except ValueError:
            print("Warning: Could not parse date from filename. Using today's date.")
    
    return filename, datetime.now().strftime('%B %d, %Y')

def create_database(app):
    """Creates the database and tables from the models."""
    with app.app_context():
        # The path is now relative to the instance folder of the app
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing database '{db_path}'.")
        db.create_all()
        print("Database structure created successfully from models.")

def seed_data(app, client_name, report_date, advisor_csv_file):
    """Seeds the database with data from CSV files."""
    with app.app_context():
        client = ClientInfo(name=client_name, report_date=report_date)
        db.session.add(client)
        print(f"Seeding client: {client_name} with report date: {report_date}")

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

        # --- VMs (Case-Insensitive Mapping) ---
        vm_map = {}
        with open(VMS_CSV, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sub_obj = sub_name_map.get(row['SUBSCRIPTION'].upper())
                if sub_obj:
                    rg_obj = rg_map.get((row['RESOURCE GROUP'].upper(), sub_obj.id))
                    if rg_obj:
                        vm = VM(name=row['NAME'], location=row['LOCATION'], status=row['STATUS'], 
                                os=row['OPERATING SYSTEM'], size=row['SIZE'], public_ip=row['PUBLIC IP ADDRESS'], 
                                disks=row['DISKS'], resource_group=rg_obj)
                        db.session.add(vm)
                        vm_map[vm.name.upper()] = vm
        db.session.commit()
        print(f"Seeded {len(vm_map)} VMs.")

        # --- VMSS (Case-Insensitive Mapping) ---
        vmss_map = {}
        with open(VMSS_CSV, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sub_obj = sub_name_map.get(row['SUBSCRIPTION'].upper())
                if sub_obj:
                    rg_obj = rg_map.get((row['RESOURCE GROUP'].upper(), sub_obj.id))
                    if rg_obj:
                        vmss = VMSS(name=row['NAME'], location=row['LOCATION'], provisioning_state=row['PROVISIONING STATE'],
                                    status=row['STATUS'], os=row['OPERATING SYSTEM'], size=row['SIZE'], 
                                    instances=row['INSTANCES'], orchestration_mode=row['ORCHESTRATION MODE'], 
                                    public_ip=row['PUBLIC IP ADDRESS'], resource_group=rg_obj)
                        db.session.add(vmss)
                        vmss_map[vmss.name.upper()] = vmss
        db.session.commit()
        print(f"Seeded {len(vmss_map)} VM Scale Sets.")
        
        # --- Recommendations (with Case-Insensitive Linking) ---
        rec_type_map = {}
        rec_count, skipped_count = 0, 0
        with open(advisor_csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Type'] == 'Subscription' and row['Category'] == 'Cost':
                    skipped_count += 1
                    continue

                rec_text = row['Recommendation']
                rec_type = rec_type_map.get(rec_text)
                if not rec_type:
                    rec_type = RecommendationType(text=rec_text, category=row['Category'], impact=row['Business Impact'])
                    db.session.add(rec_type)
                    db.session.flush() 
                    rec_type_map[rec_text] = rec_type
                
                resource_name_from_csv = row['Resource Name']
                resource_type_str = row['Type']
                
                resource_id = None
                correctly_cased_resource_name = resource_name_from_csv 

                resource_obj = None
                if resource_type_str == 'Virtual machine':
                    resource_obj = vm_map.get(resource_name_from_csv.upper())
                elif resource_type_str == 'Virtual machine scale set':
                    resource_obj = vmss_map.get(resource_name_from_csv.upper())
                
                if resource_obj:
                    resource_id = resource_obj.id
                    correctly_cased_resource_name = resource_obj.name
                
                savings_str = row.get('Potential Annual Cost Savings', '0').replace(',', '')
                savings = float(savings_str) if savings_str else 0.0
                
                rec_instance = RecommendationInstance(
                    recommendation_type=rec_type,
                    resource_id=resource_id,
                    resource_type=resource_type_str,
                    subscription_name=row['Subscription Name'].split(' (')[0],
                    resource_group_name=row['Resource Group'],
                    resource_name=correctly_cased_resource_name,
                    potential_savings=savings
                )
                db.session.add(rec_instance)
                rec_count += 1
        
        db.session.commit()
        print(f"Seeded {rec_count} recommendation instances.")
        if skipped_count > 0:
            print(f"Skipped {skipped_count} redundant subscription-level cost recommendations.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Seed Azure Advisor report data into a SQLite database using SQLAlchemy.")
    parser.add_argument("client_name", type=str, help="The name of the client for this report.")
    args = parser.parse_args()

    # Create an app instance for context
    flask_app = create_app()
    
    advisor_file, report_date = find_advisor_file()
    
    create_database(flask_app)
    seed_data(flask_app, args.client_name, report_date, advisor_file)
    
    print("\nDatabase seeding complete. You can now run 'python run.py'.")
