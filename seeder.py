import sqlite3
import csv
import os
import argparse
import glob
import re
from datetime import datetime

# --- Configuration ---
DB_FILE = 'report.db'
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
    
    print("Warning: Could not find a date in the Advisor filename. Using today's date.")
    return filename, datetime.now().strftime('%B %d, %Y')


def create_database():
    """Creates the SQLite database and the necessary tables with relational schema."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Removed existing database '{DB_FILE}'.")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create Tables
    cursor.execute('CREATE TABLE client_info (id INTEGER PRIMARY KEY, name TEXT NOT NULL, report_date TEXT)')
    cursor.execute('CREATE TABLE subscriptions (id INTEGER PRIMARY KEY, name TEXT UNIQUE, subscription_id_guid TEXT UNIQUE)')
    cursor.execute('CREATE TABLE resource_groups (id INTEGER PRIMARY KEY, name TEXT, subscription_id INTEGER, FOREIGN KEY(subscription_id) REFERENCES subscriptions(id), UNIQUE(name, subscription_id))')
    cursor.execute('CREATE TABLE vms (id INTEGER PRIMARY KEY, name TEXT, location TEXT, status TEXT, os TEXT, size TEXT, public_ip TEXT, disks INTEGER, resource_group_id INTEGER, FOREIGN KEY(resource_group_id) REFERENCES resource_groups(id))')
    
    cursor.execute('''
    CREATE TABLE vmss (
        id INTEGER PRIMARY KEY,
        name TEXT,
        location TEXT,
        provisioning_state TEXT,
        status TEXT,
        os TEXT,
        size TEXT,
        instances INTEGER,
        orchestration_mode TEXT,
        public_ip TEXT,
        resource_group_id INTEGER,
        FOREIGN KEY(resource_group_id) REFERENCES resource_groups(id)
    )''')
    print("Table 'vmss' created correctly.")

    cursor.execute('CREATE TABLE recommendation_types (id INTEGER PRIMARY KEY, text TEXT UNIQUE, category TEXT, impact TEXT)')
    cursor.execute('CREATE TABLE recommendation_instances (id INTEGER PRIMARY KEY, recommendation_type_id INTEGER, resource_id INTEGER, resource_type TEXT, subscription_name TEXT, resource_group_name TEXT, resource_name TEXT, potential_savings REAL, FOREIGN KEY(recommendation_type_id) REFERENCES recommendation_types(id))')
    
    conn.commit()
    conn.close()
    print("Relational database structure created successfully.")

def seed_data(client_name, report_date, advisor_csv_file):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('INSERT INTO client_info (id, name, report_date) VALUES (1, ?, ?)', (client_name, report_date))
    print(f"Seeded client: {client_name} with report date: {report_date}")

    sub_name_to_pk = {}
    with open(SUBSCRIPTIONS_CSV, 'r', encoding='utf-8-sig') as f:
        next(f, None)
        reader = csv.DictReader(f)
        for row in reader:
            sub_name = row['SUBSCRIPTION NAME']
            sub_guid = row['SUBSCRIPTION ID']
            cursor.execute('INSERT INTO subscriptions (name, subscription_id_guid) VALUES (?, ?)', (sub_name, sub_guid))
            sub_pk = cursor.lastrowid
            sub_name_to_pk[sub_name.upper()] = sub_pk
    print(f"Seeded {len(sub_name_to_pk)} subscriptions.")
    
    rg_name_sub_pk_to_pk = {}
    with open(RESOURCE_GROUPS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub_pk = sub_name_to_pk.get(row['SUBSCRIPTION'].upper())
            if sub_pk:
                rg_name = row['NAME']
                cursor.execute('INSERT INTO resource_groups (name, subscription_id) VALUES (?, ?)', (rg_name, sub_pk))
                rg_pk = cursor.lastrowid
                rg_name_sub_pk_to_pk[(rg_name.upper(), sub_pk)] = rg_pk
    print(f"Seeded {len(rg_name_sub_pk_to_pk)} resource groups.")

    vm_name_to_pk = {}
    with open(VMS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub_pk = sub_name_to_pk.get(row['SUBSCRIPTION'].upper())
            if sub_pk:
                rg_pk = rg_name_sub_pk_to_pk.get((row['RESOURCE GROUP'].upper(), sub_pk))
                if rg_pk:
                    cursor.execute('INSERT INTO vms (name, location, status, os, size, public_ip, disks, resource_group_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                   (row['NAME'], row['LOCATION'], row['STATUS'], row['OPERATING SYSTEM'], row['SIZE'], row['PUBLIC IP ADDRESS'], row['DISKS'], rg_pk))
                    vm_name_to_pk[row['NAME']] = cursor.lastrowid
    print(f"Seeded {len(vm_name_to_pk)} VMs.")

    vmss_name_to_pk = {}
    with open(VMSS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub_pk = sub_name_to_pk.get(row['SUBSCRIPTION'].upper())
            if sub_pk:
                rg_pk = rg_name_sub_pk_to_pk.get((row['RESOURCE GROUP'].upper(), sub_pk))
                if rg_pk:
                     cursor.execute('INSERT INTO vmss (name, location, provisioning_state, status, os, size, instances, orchestration_mode, public_ip, resource_group_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                   (row['NAME'], row['LOCATION'], row['PROVISIONING STATE'], row['STATUS'], row['OPERATING SYSTEM'], row['SIZE'], row['INSTANCES'], row['ORCHESTRATION MODE'], row['PUBLIC IP ADDRESS'], rg_pk))
                     vmss_name_to_pk[row['NAME']] = cursor.lastrowid
    print(f"Seeded {len(vmss_name_to_pk)} VM Scale Sets.")
    
    rec_text_to_pk = {}
    rec_count = 0
    skipped_count = 0
    with open(advisor_csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Type'] == 'Subscription' and row['Category'] == 'Cost':
                skipped_count += 1
                continue

            rec_text = row['Recommendation']
            rec_type_pk = rec_text_to_pk.get(rec_text)
            if not rec_type_pk:
                cursor.execute('INSERT INTO recommendation_types (text, category, impact) VALUES (?, ?, ?)',
                               (rec_text, row['Category'], row['Business Impact']))
                rec_type_pk = cursor.lastrowid
                rec_text_to_pk[rec_text] = rec_type_pk
            
            resource_name = row['Resource Name']
            resource_type = row['Type']
            resource_id = None
            
            if resource_type == 'Virtual machine':
                resource_id = vm_name_to_pk.get(resource_name)
            elif resource_type == 'Virtual machine scale set':
                resource_id = vmss_name_to_pk.get(resource_name)
            
            # **MODIFIED LOGIC**: Parse the subscription name from the combined string
            subscription_name_from_csv = row['Subscription Name']
            clean_subscription_name = subscription_name_from_csv.split(' (')[0]

            savings_str = row.get('Potential Annual Cost Savings', '0').replace(',', '')
            savings = float(savings_str) if savings_str else 0.0
            cursor.execute('INSERT INTO recommendation_instances (recommendation_type_id, resource_id, resource_type, subscription_name, resource_group_name, resource_name, potential_savings) VALUES (?, ?, ?, ?, ?, ?, ?)',
                           (rec_type_pk, resource_id, resource_type, clean_subscription_name, row['Resource Group'], resource_name, savings))
            rec_count += 1

    print(f"Seeded {rec_count} recommendation instances.")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} redundant subscription-level cost recommendations.")
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Seed Azure Advisor report data into a SQLite database.")
    parser.add_argument("client_name", type=str, help="The name of the client for this report.")
    args = parser.parse_args()

    advisor_file, report_date = find_advisor_file()
    
    create_database()
    seed_data(args.client_name, report_date, advisor_file)
    print("\nDatabase seeding complete. You can now run 'app.py'.")
