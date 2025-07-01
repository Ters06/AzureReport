import csv
from .models import RecommendationType, RecommendationInstance

def seed_recommendations(db, context, advisor_csv_file):
    """Seeds recommendation data and links it to existing resources."""
    vm_map = context.get('vm_map', {})
    vmss_map = context.get('vmss_map', {})
    storage_map = context.get('storage_map', {})

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
            resource_type_lower = resource_type_str.lower()

            if resource_type_lower == 'virtual machine':
                resource_obj = vm_map.get(resource_name_from_csv.upper())
            elif resource_type_lower == 'virtual machine scale set':
                resource_obj = vmss_map.get(resource_name_from_csv.upper())
            elif resource_type_lower == 'storage account':
                resource_obj = storage_map.get(resource_name_from_csv.upper())
            
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
                potential_savings=savings,
                # FIX: Store the full resource URI from the CSV
                resource_uri=row.get('Resource Id')
            )
            db.session.add(rec_instance)
            rec_count += 1
    
    print(f"Seeded {rec_count} recommendation instances.")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} redundant subscription-level cost recommendations.")
