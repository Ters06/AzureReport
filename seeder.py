import os
import argparse
from datetime import datetime
import re
import glob
from app import create_app, db
from app.services import get_service_configs

def find_advisor_file():
    """Finds the advisor CSV file and extracts the date from its name."""
    files = glob.glob('Advisor*.csv')
    if not files:
        print("Error: No Advisor CSV file found.")
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
            print("Warning: Could not parse date from filename.")
    return filename, datetime.now().strftime('%B %d, %Y')

def create_database(app):
    """Creates the database and tables from the models."""
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing database '{db_path}'.")
        db.create_all()
        print("Database structure created successfully from models.")

def run_seeders(app, client_name, report_date, advisor_csv_file):
    """Dynamically discovers and runs all service seeders."""
    with app.app_context():
        from app.services.core.models import ClientInfo
        client_info = ClientInfo(name=client_name, report_date=report_date)
        db.session.add(client_info)
        db.session.commit()

        service_configs = get_service_configs()
        seeder_context = {}
        seed_order = ['core', 'virtual_machines', 'vm_scale_sets', 'storage_accounts', 'recommendations']
        
        for service_key in seed_order:
            config = next((c for c in service_configs if c.get('KEY') == service_key), None)
            if config and config.get('SEEDER_FUNC'):
                print(f"--- Seeding {config.get('NAME', service_key)} ---")
                csv_file = config.get('CSV_FILE')
                if csv_file and not os.path.exists(csv_file):
                    print(f"Warning: {csv_file} not found for service '{service_key}'. Skipping.")
                    continue
                
                if service_key == 'recommendations':
                    config['SEEDER_FUNC'](db, seeder_context, advisor_csv_file)
                else:
                    config['SEEDER_FUNC'](db, seeder_context)
            
        db.session.commit()
        print("\nAll seeders completed successfully.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Seed Azure Advisor report data into a SQLite database.")
    parser.add_argument("client_name", type=str, help="The name of the client for this report.")
    args = parser.parse_args()

    flask_app = create_app()
    advisor_file, report_date = find_advisor_file()
    
    create_database(flask_app)
    run_seeders(flask_app, args.client_name, report_date, advisor_file)
    
    print("\nDatabase seeding complete. You can now run 'python run.py'.")
