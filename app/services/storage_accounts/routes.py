from flask import Blueprint, render_template, request
from sqlalchemy import func, desc, asc
from app.db import db
from .models import StorageAccount
from app.services.core.models import Subscription, ResourceGroup
from app.services.recommendations.models import RecommendationInstance, RecommendationType

storage_bp = Blueprint('storage', __name__, url_prefix='/storage-accounts')
ALLOWED_LIMITS = [10, 25, 50, 100]

def get_distinct_values(query, model, column_name):
    """Helper to get distinct values from the current query context."""
    return [row[0] for row in query.with_entities(getattr(model, column_name)).distinct().filter(getattr(model, column_name).isnot(None)).order_by(getattr(model, column_name)).all()]

@storage_bp.route('/')
def storage_accounts_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 25, type=int)
    if limit not in ALLOWED_LIMITS: limit = 25
    
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    
    active_filters = {}
    base_query = db.session.query(StorageAccount).join(StorageAccount.resource_group).join(ResourceGroup.subscription)

    for col in ['location', 'sku', 'kind', 'subscription_name', 'resource_group_name']:
        filter_values = request.args.get(col)
        if filter_values:
            values_list = filter_values.split(',')
            active_filters[col] = values_list
            if col == 'subscription_name':
                base_query = base_query.filter(Subscription.name.in_(values_list))
            elif col == 'resource_group_name':
                base_query = base_query.filter(ResourceGroup.name.in_(values_list))
            else:
                base_query = base_query.filter(getattr(StorageAccount, col).in_(values_list))
    
    recs_subquery = db.session.query(
        RecommendationInstance.resource_id,
        func.count(RecommendationInstance.id).label('recommendation_count'),
        func.sum(RecommendationInstance.potential_savings).label('potential_savings')
    ).filter(func.lower(RecommendationInstance.resource_type) == 'storage account').group_by(RecommendationInstance.resource_id).subquery()

    final_query = base_query.add_columns(
        Subscription.name.label('subscription_name'),
        ResourceGroup.name.label('resource_group_name'),
        func.ifnull(recs_subquery.c.recommendation_count, 0).label('recommendation_count'),
        func.ifnull(recs_subquery.c.potential_savings, 0).label('potential_savings')
    ).outerjoin(recs_subquery, StorageAccount.id == recs_subquery.c.resource_id)

    sort_column_map = {
        'name': StorageAccount.name, 'location': StorageAccount.location, 'sku': StorageAccount.sku, 'kind': StorageAccount.kind,
        'recommendation_count': 'recommendation_count', 'potential_savings': 'potential_savings'
    }
    sort_column = sort_column_map.get(sort_by, StorageAccount.name)
    order_logic = desc(sort_column) if sort_order == 'desc' else asc(sort_column)
    final_query = final_query.order_by(order_logic)

    paginated_results = final_query.paginate(page=page, per_page=limit, error_out=False)
    
    headers = [
        {'label': 'Name', 'key': 'name', 'sortable': True, 'is_link': True, 'filterable': False},
        {'label': 'Subscription', 'key': 'subscription_name', 'sortable': False, 'filterable': True},
        {'label': 'Resource Group', 'key': 'resource_group_name', 'sortable': False, 'filterable': True},
        {'label': 'Location', 'key': 'location', 'sortable': True, 'filterable': True},
        {'label': 'SKU', 'key': 'sku', 'sortable': True, 'filterable': True},
        {'label': 'Kind', 'key': 'kind', 'sortable': True, 'filterable': True},
        {'label': '# Recs', 'key': 'recommendation_count', 'sortable': True, 'align': 'center', 'filterable': False},
        {'label': 'Savings', 'key': 'potential_savings', 'sortable': True, 'align': 'right', 'format': 'currency', 'filterable': False},
    ]

    rows = []
    for sa, sub_name, rg_name, rec_count, savings in paginated_results.items:
        rows.append({
            'name': sa.name, 'subscription_name': sub_name, 'resource_group_name': rg_name,
            'location': sa.location, 'sku': sa.sku, 'kind': sa.kind,
            'recommendation_count': rec_count, 'potential_savings': savings,
            'resource_type': 'Storage account', 'resource_id': sa.id
        })
        
    filter_data = {
        'location': get_distinct_values(base_query, StorageAccount, 'location'),
        'sku': get_distinct_values(base_query, StorageAccount, 'sku'),
        'kind': get_distinct_values(base_query, StorageAccount, 'kind'),
        'subscription_name': [s.name for s in Subscription.query.order_by(Subscription.name).all()],
        'resource_group_name': get_distinct_values(base_query, ResourceGroup, 'name'),
    }

    return render_template('storage_accounts.html', 
                           headers=headers, rows=rows, filter_data=filter_data, active_filters=active_filters,
                           page=page, total_pages=paginated_results.pages, total_items=paginated_results.total, 
                           limit=limit, sort_by=sort_by, sort_order=sort_order)

@storage_bp.route('/<resource_name>')
def storage_account_detail(resource_name):
    storage_account = StorageAccount.query.filter_by(name=resource_name).first_or_404()
    recommendations = RecommendationInstance.query.join(RecommendationType).filter(
        func.lower(RecommendationInstance.resource_type) == 'storage account',
        RecommendationInstance.resource_id == storage_account.id
    ).order_by(RecommendationType.impact).all()
    return render_template('storage_account_detail.html', storage_account=storage_account, recommendations=recommendations)
