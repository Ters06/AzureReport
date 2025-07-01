from flask import Flask, render_template, request, jsonify
from sqlalchemy import func
import math
import os

# Import the database object and models from our new models.py file
from models import db, ClientInfo, Subscription, ResourceGroup, VM, VMSS, RecommendationType, RecommendationInstance

# --- App Initialization ---
app = Flask(__name__)

# --- Configuration ---
# Get the absolute path of the directory where the script is located
basedir = os.path.abspath(os.path.dirname(__file__))
# Configure the database URI to use an absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'report.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the app with the database
db.init_app(app)

ALLOWED_LIMITS = [10, 25, 50, 100]

# --- Template Filters and Context Processors ---

@app.template_filter('format_currency')
def format_currency(value):
    """Formats a value as currency."""
    if value is None or value == 0:
        return "-"
    return "${:,.2f}".format(value)

@app.context_processor
def inject_global_vars():
    """Makes global context available to all templates."""
    client_info = ClientInfo.query.first()
    categories_query = db.session.query(RecommendationType.category).distinct().order_by(RecommendationType.category).all()
    
    context = {
        "nav_categories": [{'category': c[0]} for c in categories_query if c[0] is not None],
        "client_name": client_info.name if client_info else "Azure Report",
        "report_date": client_info.report_date if client_info else "N/A"
    }
    return context

# --- Main App Routes ---

@app.route('/')
def index():
    """Dashboard route."""
    # Key Metrics using SQLAlchemy queries
    total_recs = db.session.query(func.count(RecommendationInstance.id)).scalar()
    high_impact = RecommendationInstance.query.join(RecommendationType).filter(RecommendationType.impact == 'High').count()
    total_savings = db.session.query(func.sum(RecommendationInstance.potential_savings)).scalar()
    vm_count = VM.query.count()
    vmss_count = VMSS.query.count()

    return render_template('index.html',
                           total_recs=total_recs,
                           high_impact=high_impact,
                           total_savings=total_savings or 0,
                           vm_count=vm_count,
                           vmss_count=vmss_count)

@app.route('/vms')
def vms_list():
    """Paginated list of Virtual Machines."""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 25, type=int)
    if limit not in ALLOWED_LIMITS:
        limit = 25

    # Subquery to calculate recommendation counts and savings per VM
    recs_subquery = db.session.query(
        RecommendationInstance.resource_id,
        func.count(RecommendationInstance.id).label('recommendation_count'),
        func.sum(RecommendationInstance.potential_savings).label('potential_savings')
    ).filter(RecommendationInstance.resource_type == 'Virtual machine').group_by(RecommendationInstance.resource_id).subquery()

    # Main query joining VMs with the recommendation subquery
    vms_query = db.session.query(
        VM,
        func.ifnull(recs_subquery.c.recommendation_count, 0).label('recommendation_count'),
        func.ifnull(recs_subquery.c.potential_savings, 0).label('potential_savings')
    ).outerjoin(recs_subquery, VM.id == recs_subquery.c.resource_id).order_by(VM.name)
    
    vms_paginated = vms_query.paginate(page=page, per_page=limit, error_out=False)
    
    # We need to structure the data for the template
    vms_data = []
    for vm, rec_count, savings in vms_paginated.items:
        vms_data.append({
            'name': vm.name,
            'subscription_name': vm.resource_group.subscription.name,
            'resource_group_name': vm.resource_group.name,
            'os': vm.os,
            'size': vm.size,
            'status': vm.status,
            'recommendation_count': rec_count,
            'potential_savings': savings
        })

    return render_template('vms.html', vms=vms_data, 
                           page=page, total_pages=vms_paginated.pages, 
                           total_items=vms_paginated.total, limit=limit)

@app.route('/vm/<vm_name>')
def vm_detail(vm_name):
    """Detail page for a single Virtual Machine."""
    vm = VM.query.filter_by(name=vm_name).first_or_404()
    
    recs = RecommendationInstance.query.join(RecommendationType).filter(
        RecommendationInstance.resource_type == 'Virtual machine',
        RecommendationInstance.resource_id == vm.id
    ).order_by(RecommendationType.impact).all()

    return render_template('vm_detail.html', vm=vm, recommendations=recs)

@app.route('/vmss')
def vmss_list():
    """Paginated list of Virtual Machine Scale Sets."""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 25, type=int)
    if limit not in ALLOWED_LIMITS:
        limit = 25

    recs_subquery = db.session.query(
        RecommendationInstance.resource_id,
        func.count(RecommendationInstance.id).label('recommendation_count'),
        func.sum(RecommendationInstance.potential_savings).label('potential_savings')
    ).filter(RecommendationInstance.resource_type == 'Virtual machine scale set').group_by(RecommendationInstance.resource_id).subquery()

    vmss_query = db.session.query(
        VMSS,
        func.ifnull(recs_subquery.c.recommendation_count, 0).label('recommendation_count'),
        func.ifnull(recs_subquery.c.potential_savings, 0).label('potential_savings')
    ).outerjoin(recs_subquery, VMSS.id == recs_subquery.c.resource_id).order_by(VMSS.name)
    
    vmss_paginated = vmss_query.paginate(page=page, per_page=limit, error_out=False)

    vmss_data = []
    for vmss_item, rec_count, savings in vmss_paginated.items:
        vmss_data.append({
            'name': vmss_item.name,
            'subscription_name': vmss_item.resource_group.subscription.name,
            'resource_group_name': vmss_item.resource_group.name,
            'os': vmss_item.os,
            'size': vmss_item.size,
            'instances': vmss_item.instances,
            'recommendation_count': rec_count,
            'potential_savings': savings
        })

    return render_template('vmss.html', vmss=vmss_data, 
                           page=page, total_pages=vmss_paginated.pages, 
                           total_items=vmss_paginated.total, limit=limit)

@app.route('/vmss/<vmss_name>')
def vmss_detail(vmss_name):
    """Detail page for a single VM Scale Set."""
    vmss_item = VMSS.query.filter_by(name=vmss_name).first_or_404()
    
    recs = RecommendationInstance.query.join(RecommendationType).filter(
        RecommendationInstance.resource_type == 'Virtual machine scale set',
        RecommendationInstance.resource_id == vmss_item.id
    ).order_by(RecommendationType.impact).all()

    return render_template('vmss_detail.html', vmss=vmss_item, recommendations=recs)

@app.route('/recommendations')
def recommendations_list():
    """Paginated and filterable list of all recommendations."""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 25, type=int)
    if limit not in ALLOWED_LIMITS:
        limit = 25
    
    category = request.args.get('category')
    impact = request.args.get('impact')
    subscription = request.args.get('subscription')
    
    query = RecommendationInstance.query.join(RecommendationType)
    
    title_parts = []
    if impact:
        query = query.filter(func.lower(RecommendationType.impact) == func.lower(impact))
        title_parts.append(f"{impact.title()} Impact")
    if category:
        query = query.filter(func.lower(RecommendationType.category) == func.lower(category.replace('-', ' ')))
        title_parts.append(f"{category.replace('-', ' ').title()}")
    if subscription:
        query = query.filter(RecommendationInstance.subscription_name == subscription)
        title_parts.append(f"for {subscription}")
        
    page_title = " ".join(title_parts) + " Recommendations" if title_parts else "All Recommendations"

    query = query.order_by(RecommendationType.impact.desc(), RecommendationInstance.resource_name)
    
    recs_paginated = query.paginate(page=page, per_page=limit, error_out=False)

    # Add recommendation text to each instance for the template
    recs_data = []
    for rec in recs_paginated.items:
        recs_data.append({
            'resource_type': rec.resource_type,
            'resource_name': rec.resource_name,
            'impact': rec.recommendation_type.impact,
            'recommendation_text': rec.recommendation_type.text,
            'subscription_name': rec.subscription_name,
            'potential_savings': rec.potential_savings
        })

    return render_template('recommendations.html', recommendations=recs_data, 
                           page_title=page_title, page=page, 
                           total_pages=recs_paginated.pages, total_items=recs_paginated.total, limit=limit)

# --- API Routes for Charts ---

@app.route('/api/data/recommendations-summary')
def recommendations_summary():
    category_data = db.session.query(
        RecommendationType.category, func.count(RecommendationInstance.id)
    ).join(RecommendationInstance).group_by(RecommendationType.category).order_by(func.count(RecommendationInstance.id).desc()).all()
    
    impact_data = db.session.query(
        RecommendationType.impact, func.count(RecommendationInstance.id)
    ).join(RecommendationInstance).group_by(RecommendationType.impact).all()
    
    return jsonify({
        'categories': {
            'labels': [row[0] for row in category_data],
            'data': [row[1] for row in category_data]
        },
        'impacts': {
            'labels': [row[0] for row in impact_data],
            'data': [row[1] for row in impact_data]
        }
    })

@app.route('/api/data/impact-by-category/<category>')
def impact_by_category(category):
    formatted_category = category.replace('-', ' ')
    impact_data = db.session.query(
        RecommendationType.impact, func.count(RecommendationInstance.id)
    ).join(RecommendationInstance).filter(
        func.lower(RecommendationType.category) == func.lower(formatted_category)
    ).group_by(RecommendationType.impact).all()
    
    return jsonify({
        'labels': [row[0] for row in impact_data],
        'data': [row[1] for row in impact_data]
    })

@app.route('/api/data/recommendations-by-subscription/<group_by>')
def recommendations_by_subscription(group_by):
    if group_by not in ['impact', 'category']:
        return jsonify({"error": "Invalid grouping"}), 400

    grouping_attr = getattr(RecommendationType, group_by)
    
    recs_data_query = db.session.query(
        RecommendationInstance.subscription_name,
        grouping_attr,
        func.count(RecommendationInstance.id)
    ).join(RecommendationType).filter(
        RecommendationInstance.subscription_name.isnot(None),
        grouping_attr.isnot(None)
    ).group_by(RecommendationInstance.subscription_name, grouping_attr).all()

    all_subs = Subscription.query.order_by(Subscription.name).all()
    all_grouping_keys = [row[0] for row in db.session.query(grouping_attr).distinct().filter(grouping_attr.isnot(None)).order_by(grouping_attr).all()]
    
    subs_data = {sub.name: {'guid': sub.subscription_id_guid, 'counts': {key: 0 for key in all_grouping_keys}} for sub in all_subs}
    
    for sub_name, grouping_key, count in recs_data_query:
        if sub_name in subs_data and grouping_key in subs_data[sub_name]['counts']:
            subs_data[sub_name]['counts'][grouping_key] = count
            
    labels = [f"{name} ({data['guid']})" for name, data in subs_data.items()]
    datasets = {key: {"label": key, "data": []} for key in all_grouping_keys}

    for sub_name, data in subs_data.items():
        for key in all_grouping_keys:
            datasets[key]['data'].append(data['counts'].get(key, 0))
            
    return jsonify({'labels': labels, 'datasets': list(datasets.values())})

# --- Main Execution ---

if __name__ == '__main__':
    app.run(debug=True)
