from flask import Blueprint, render_template, request
from sqlalchemy import func, desc, asc
from app.db import db
from .models import VM
from app.services.core.models import Resource, ResourceGroup, Subscription
from app.services.recommendations.models import RecommendationInstance

vms_bp = Blueprint('vms', __name__, url_prefix='/vms')
ALLOWED_LIMITS = [10, 25, 50, 100]

def get_distinct_values(query, model, column_name):
    """Helper to get distinct values from the current query context."""
    return [row[0] for row in query.with_entities(getattr(model, column_name)).distinct().filter(getattr(model, column_name).isnot(None)).order_by(getattr(model, column_name)).all()]

@vms_bp.route('/')
def vms_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 25, type=int)
    if limit not in ALLOWED_LIMITS: limit = 25
    
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    
    active_filters = {}
    # FIX: Start the query from VM and explicitly join through the relationships
    base_query = db.session.query(VM).join(ResourceGroup, VM.resource_group_id == ResourceGroup.id).join(Subscription, ResourceGroup.subscription_id == Subscription.id)

    # Apply filters from URL args
    for col in ['os', 'size', 'status', 'subscription_name', 'resource_group_name']:
        filter_values = request.args.get(col)
        if filter_values:
            values_list = filter_values.split(',')
            active_filters[col] = values_list
            if col == 'subscription_name':
                base_query = base_query.filter(Subscription.name.in_(values_list))
            elif col == 'resource_group_name':
                base_query = base_query.filter(ResourceGroup.name.in_(values_list))
            else:
                base_query = base_query.filter(getattr(VM, col).in_(values_list))
    
    recs_subquery = db.session.query(
        RecommendationInstance.resource_id,
        func.count(RecommendationInstance.id).label('recommendation_count'),
        func.sum(RecommendationInstance.potential_savings).label('potential_savings')
    ).group_by(RecommendationInstance.resource_id).subquery()

    # Add columns from the already-joined tables
    final_query = base_query.add_columns(
            Subscription.name.label('subscription_name'),
            ResourceGroup.name.label('resource_group_name'),
            func.ifnull(recs_subquery.c.recommendation_count, 0).label('recommendation_count'),
            func.ifnull(recs_subquery.c.potential_savings, 0).label('potential_savings')
        ).outerjoin(recs_subquery, VM.id == recs_subquery.c.resource_id)

    sort_column_map = {
        'name': VM.name, 'os': VM.os, 'size': VM.size, 'status': VM.status,
        'recommendation_count': 'recommendation_count', 'potential_savings': 'potential_savings'
    }
    sort_column = sort_column_map.get(sort_by, VM.name)
    order_logic = desc(sort_column) if sort_order == 'desc' else asc(sort_column)
    final_query = final_query.order_by(order_logic)

    paginated_results = final_query.paginate(page=page, per_page=limit, error_out=False)
    
    headers = [
        {'label': 'Name', 'key': 'name', 'sortable': True, 'is_link': True, 'filterable': False},
        {'label': 'Subscription', 'key': 'subscription_name', 'sortable': False, 'filterable': True},
        {'label': 'Resource Group', 'key': 'resource_group_name', 'sortable': False, 'filterable': True},
        {'label': 'OS', 'key': 'os', 'sortable': True, 'filterable': True},
        {'label': 'Size', 'key': 'size', 'sortable': True, 'filterable': True},
        {'label': 'Status', 'key': 'status', 'sortable': True, 'filterable': True},
        {'label': '# Recs', 'key': 'recommendation_count', 'sortable': True, 'align': 'center', 'filterable': False},
        {'label': 'Savings', 'key': 'potential_savings', 'sortable': True, 'align': 'right', 'format': 'currency', 'filterable': False},
    ]

    rows = []
    for vm, sub_name, rg_name, rec_count, savings in paginated_results.items:
        rows.append({
            'resource': vm, # Pass the whole vm object which inherits from Resource
            'name': vm.name, 'subscription_name': sub_name, 'resource_group_name': rg_name,
            'os': vm.os, 'size': vm.size, 'status': vm.status,
            'recommendation_count': rec_count, 'potential_savings': savings
        })
        
    filter_data = {
        'os': get_distinct_values(base_query, VM, 'os'),
        'size': get_distinct_values(base_query, VM, 'size'),
        'status': get_distinct_values(base_query, VM, 'status'),
        'subscription_name': [s.name for s in Subscription.query.order_by(Subscription.name).all()],
        'resource_group_name': get_distinct_values(base_query, ResourceGroup, 'name'),
    }

    return render_template('vms.html', 
                           headers=headers, rows=rows, filter_data=filter_data, active_filters=active_filters,
                           page=page, total_pages=paginated_results.pages, total_items=paginated_results.total, 
                           limit=limit, sort_by=sort_by, sort_order=sort_order)

@vms_bp.route('<path:resource_id>')
def vm_detail(resource_id):
    vm = VM.query.filter_by(id=f"/{resource_id}").first_or_404()
    recommendations = RecommendationInstance.query.filter_by(resource_id=vm.id).all()
    return render_template('vm_detail.html', vm=vm, recommendations=recommendations)
