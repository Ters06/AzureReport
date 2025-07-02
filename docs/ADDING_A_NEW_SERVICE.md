# Guide: How to Add a New Azure Service

The application is built with a modular "plugin" architecture that makes adding support for new Azure services straightforward. This guide will walk you through the process.

## Overview

Each Azure service is treated as a self-contained plugin located in its own subdirectory within `app/services/`. To add a new service, you will create a new folder here and populate it with a few standard files that define the service's data model, data seeding logic, web pages, and configuration.

Let's walk through adding a hypothetical **"Key Vault"** service.

### Step 1: Create the Service Directory

Create a new folder inside `app/services/`. The name should be a short, descriptive, lowercase identifier.

```
/app
  /services
    /core
    /virtual_machines
    /storage_accounts
    /key_vaults/  <-- NEW FOLDER
```

### Step 2: Create the Database Model

Inside your new `key_vaults` folder, create a `models.py` file. This file will define the database table for your new resource.

The model **must inherit** from the central `Resource` model to ensure it's properly integrated into the normalized database schema.

**`app/services/key_vaults/models.py`:**
```python
from app import db
from app.services.core.models import Resource

class KeyVault(Resource):
    __tablename__ = 'key_vaults'
    
    # The primary key, which is the full Azure Resource ID.
    # This also acts as a foreign key to the parent 'resources' table.
    id = db.Column(db.String, db.ForeignKey('resources.id'), primary_key=True)
    
    # Add columns specific to Key Vaults
    sku_name = db.Column(db.String)
    enable_purge_protection = db.Column(db.Boolean)
    
    # This tells SQLAlchemy how to handle the inheritance.
    # The value must match the 'Type' column from the Azure CSV export.
    __mapper_args__ = {
        'polymorphic_identity': 'Key vault' 
    }
```

### Step 3: Create the Seeder

Next, create a `seeder.py` file in the `key_vaults` folder. This script will contain the logic to read your `AzureKeyVaults.csv` file and populate the database.

**`app/services/key_vaults/seeder.py`:**
```python
import csv
import os
from .models import KeyVault

# Assumes a CSV file named 'AzureKeyVaults.csv' is in the root directory
KEY_VAULTS_CSV = 'AzureKeyVaults.csv'

def seed_key_vaults(db, context):
    if not os.path.exists(KEY_VAULTS_CSV):
        print(f"Warning: {KEY_VAULTS_CSV} not found. Skipping Key Vault seeding.")
        return

    # Get the maps created by the 'core' seeder from the shared context
    rg_map = context.get('rg_map', {})
    sub_map = context.get('sub_map', {})

    with open(KEY_VAULTS_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub_obj = sub_map.get(row['SUBSCRIPTION'].upper())
            if sub_obj:
                # Build the Resource Group ID key to look up the RG object
                rg_id_key = f"/subscriptions/{sub_obj.id}/resourceGroups/{row['RESOURCE GROUP']}".lower()
                rg_obj = rg_map.get(rg_id_key)
                
                if rg_obj:
                    # Build the full, unique Azure Resource ID for the Key Vault
                    kv_id = f"{rg_obj.id}/providers/microsoft.keyvault/vaults/{row['NAME']}".lower()
                    
                    # Create the KeyVault object with all parent (Resource) and child attributes
                    key_vault = KeyVault(
                        id=kv_id,
                        name=row['NAME'],
                        type='Key vault', # Must match polymorphic_identity in the model
                        location=row['LOCATION'],
                        resource_group_id=rg_obj.id,
                        sku_name=row['SKU NAME'],
                        enable_purge_protection=row['PURGE PROTECTION'] == 'Enabled'
                    )
                    db.session.add(key_vault)
    
    db.session.commit()
    print(f"Seeded Key Vaults successfully.")
```

### Step 4: Create the Routes and Templates

Create a `routes.py` file to define the web pages for your service (e.g., a list page and a detail page). You can copy the structure from one of the existing service route files (like `virtual_machines/routes.py`) and adapt it for Key Vaults.

You will also need to create the corresponding HTML templates (`key_vaults.html`, `key_vault_detail.html`) in the `app/templates/` directory.

### Step 5: Create the Configuration File

Create an `__init__.py` file in your `key_vaults` folder. This file acts as the "manifest" for your service plugin, telling the main application how to use it.

**`app/services/key_vaults/__init__.py`:**
```python
from .routes import key_vaults_bp # Assumes your blueprint is named this
from .seeder import seed_key_vaults

SERVICE_CONFIG = {
    'KEY': 'key_vaults',
    'NAME': 'Key Vaults',
    'BLUEPRINT': key_vaults_bp,
    'MODEL_MODULES': ['.services.key_vaults.models'],
    'SEEDER_FUNC': seed_key_vaults,
    'CSV_FILE': 'AzureKeyVaults.csv',
    'SHOW_IN_NAV': True,
    'NAV_ORDER': 4, # Controls the order in the navigation dropdown
    'LIST_ROUTE': 'key_vaults.key_vaults_list', # The endpoint for the list page
    'DETAIL_ROUTE': 'key_vaults.key_vault_detail', # The endpoint for the detail page
    'RESOURCE_TYPE': 'Key vault' # Must match the polymorphic_identity
}
```

### Step 6: Update the Main Seeder

Finally, open the main `seeder.py` file in the project root and add your new service key (`'key_vaults'`) to the `seed_order` list. This ensures it runs in the correct sequence.

```python
# In seeder.py
seed_order = [
    'core', 
    'virtual_machines', 
    'vm_scale_sets', 
    'storage_accounts', 
    'key_vaults', # <-- ADD YOUR NEW SERVICE HERE
    'recommendations' # Recommendations should always be last
]
```

That's it! After placing your `AzureKeyVaults.csv` in the root directory and re-running the seeder, the application will automatically discover and integrate your new service, including adding it to the dashboard, navigation, and search results.
