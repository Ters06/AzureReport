import csv
import os
from .models import RecommendationType, RecommendationInstance

def get_provider_namespace(resource_type):
    """
    Maps a user-friendly resource type from the Advisor CSV to its
    official Azure provider namespace string.
    """
    # This mapping is crucial for building the correct Azure Resource ID.
    mapping = {
        'virtual machine': 'microsoft.compute/virtualmachines',
        'virtual machine scale set': 'microsoft.compute/virtualmachinescalesets',
        'storage account': 'microsoft.storage/storageaccounts',
        # As you add support for new services, add their mappings here.
        # e.g., 'public ip address': 'microsoft.network/publicipaddresses'
    }
    return mapping.get(resource_type.lower())

def seed_recommendations(db, context, advisor_csv_file):
    """Seeds recommendation data and links it to existing resources."""
    if not advisor_csv_file or not os.path.exists(advisor_csv_file):
        print("Error: Advisor CSV file not found. Skipping recommendations.")
        return
    
    rec_type_map = {}
    rec_count, skipped_count = 0, 0
    with open(advisor_csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Filter for redundant subscription-level cost recommendations
            if row['Type'] == 'Subscription' and row['Category'] == 'Cost':
                skipped_count += 1
                continue

            # --- FIX: Build the Resource ID from the row data ---
            subscription_id = row.get('Subscription ID')
            resource_group = row.get('Resource Group')
            resource_name = row.get('Resource Name')
            resource_type = row.get('Type')

            # If any of the essential parts are missing, we can't build the ID.
            if not all([subscription_id, resource_group, resource_name, resource_type]):
                skipped_count += 1
                continue
            
            provider_namespace = get_provider_namespace(resource_type)
            
            # If we don't know how to map this resource type, skip it for now.
            if not provider_namespace:
                skipped_count += 1
                continue

            # Construct the full, lowercase Azure Resource ID
            resource_id = (
                f"/subscriptions/{subscription_id}"
                f"/resourceGroups/{resource_group}"
                f"/providers/{provider_namespace}"
                f"/{resource_name}"
            ).lower()


            # --- Seed the recommendation type ---
            rec_text = row['Recommendation']
            rec_type = rec_type_map.get(rec_text)
            if not rec_type:
                rec_type = RecommendationType(text=rec_text, category=row['Category'], impact=row['Business Impact'])
                db.session.add(rec_type)
                db.session.flush() 
                rec_type_map[rec_text] = rec_type
            
            savings_str = row.get('Potential Annual Cost Savings', '0').replace(',', '')
            savings = float(savings_str) if savings_str else 0.0
            
            # --- Seed the recommendation instance with the constructed ID ---
            rec_instance = RecommendationInstance(
                recommendation_type_id=rec_type.id, 
                resource_id=resource_id,
                potential_savings=savings
            )
            db.session.add(rec_instance)
            rec_count += 1
    
    db.session.commit()
    print(f"Seeded {rec_count} recommendation instances.")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} unlinked or un-mappable recommendations.")
