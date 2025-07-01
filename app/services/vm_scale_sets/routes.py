from flask import Blueprint, render_template, request
from sqlalchemy import func, desc, asc
from app.db import db
from .models import VMSS
from app.services.core.models import Subscription, ResourceGroup
from app.services.recommendations.models import RecommendationInstance, RecommendationType

vmss_bp = Blueprint('vmss', __name__, url_prefix='/vmss')
ALLOWED_LIMITS = [10, 25, 50, 100]

def get_distinct_values(query, model, column_name):
    """Helper to get distinct values from the current query context."""
    return [row[0] for row in query.with_entities(getattr(model, column_name)).distinct().filter(getattr(model, column_name).isnot(None)).order_by(getattr(model, column_name)).all()]

@vmss_bp.route('/')
def vmss_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 25, type=int)
    if limit not in ALLOWED_LIMITS: limit = 25
    
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')

    active_filters = {}
    base_query = db.session.query(VMSS).join(VMSS.resource_group).join(ResourceGroup.subscription)

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
                base_query = base_query.filter(getattr(VMSS, col).in_(values_list))

    recs_subquery = db.session.query(
        RecommendationInstance.resource_id,
        func.count(RecommendationInstance.id).label('recommendation_count'),
        func.sum(RecommendationInstance.potential_savings).label('potential_savings')
    ).filter(func.lower(RecommendationInstance.resource_type) == 'virtual machine scale set').group_by(RecommendationInstance.resource_id).subquery()

    final_query = base_query.add_columns(
        Subscription.name.label('subscription_name'),
        ResourceGroup.name.label('resource_group_name'),
        func.ifnull(recs_subquery.c.recommendation_count, 0).label('recommendation_count'),
        func.ifnull(recs_subquery.c.potential_savings, 0).label('potential_savings')
    ).outerjoin(recs_subquery, VMSS.id == recs_subquery.c.resource_id)

    sort_column_map = {
        'name': VMSS.name, 'os': VMSS.os, 'size': VMSS.size, 'instances': VMSS.instances, 'status': VMSS.status,
        'recommendation_count': 'recommendation_count', 'potential_savings': 'potential_savings'
    }
    sort_column = sort_column_map.get(sort_by, VMSS.name)
    
    order_logic = desc(sort_column) if sort_order == 'desc' else asc(sort_column)
    final_query = final_query.order_by(order_logic)
    
    paginated_results = final_query.paginate(page=page, per_page=limit, error_out=False)

    headers = [
        {'label': 'Name', 'key': 'name', 'sortable': True, 'is_link': True, 'filterable': False},
        {'label': 'Subscription', 'key': 'subscription_name', 'sortable': False, 'filterable': True},
        {'label': 'Resource Group', 'key': 'resource_group_name', 'sortable': False, 'filterable': True},
        {'label': 'OS', 'key': 'os', 'sortable': True, 'filterable': True},
        {'label': 'Size', 'key': 'size', 'sortable': True, 'filterable': True},
        {'label': 'Instances', 'key': 'instances', 'sortable': True, 'align': 'center', 'filterable': False},
        {'label': 'Status', 'key': 'status', 'sortable': True, 'filterable': True},
        {'label': '# Recs', 'key': 'recommendation_count', 'sortable': True, 'align': 'center', 'filterable': False},
        {'label': 'Savings', 'key': 'potential_savings', 'sortable': True, 'align': 'right', 'format': 'currency', 'filterable': False},
    ]

    rows = []
    for vmss, sub_name, rg_name, rec_count, savings in paginated_results.items:
        rows.append({
            'name': vmss.name, 'subscription_name': sub_name, 'resource_group_name': rg_name,
            'os': vmss.os, 'size': vmss.size, 'instances': vmss.instances, 'status': vmss.status,
            'recommendation_count': rec_count, 'potential_savings': savings,
            'resource_type': 'Virtual machine scale set', 'resource_id': vmss.id
        })
        
    filter_data = {
        'os': get_distinct_values(base_query, VMSS, 'os'),
        'size': get_distinct_values(base_query, VMSS, 'size'),
        'status': get_distinct_values(base_query, VMSS, 'status'),
        'subscription_name': [s.name for s in Subscription.query.order_by(Subscription.name).all()],
        'resource_group_name': get_distinct_values(base_query, ResourceGroup, 'name'),
    }

    return render_template('vmss.html', 
                           headers=headers, rows=rows, filter_data=filter_data, active_filters=active_filters,
                           page=page, total_pages=paginated_results.pages, total_items=paginated_results.total, 
                           limit=limit, sort_by=sort_by, sort_order=sort_order)

@vmss_bp.route('/<resource_name>')
def vmss_detail(resource_name):
    vmss_item = VMSS.query.filter_by(name=resource_name).first_or_404()
    recommendations = RecommendationInstance.query.join(RecommendationType).filter(
        func.lower(RecommendationInstance.resource_type) == 'virtual machine scale set',
        RecommendationInstance.resource_id == vmss_item.id
    ).order_by(RecommendationType.impact).all()
    return render_template('vmss_detail.html', vmss=vmss_item, recommendations=recommendations)
