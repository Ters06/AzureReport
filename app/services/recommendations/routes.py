from flask import Blueprint, render_template, request, current_app
from sqlalchemy import func, desc, asc
from app.db import db
from .models import RecommendationInstance, RecommendationType
from app.services.core.models import Resource, ResourceGroup, Subscription

recs_bp = Blueprint('recs', __name__, url_prefix='/recommendations')
ALLOWED_LIMITS = [10, 25, 50, 100]

def get_distinct_values(query, model, column_name):
    """Helper to get distinct values from the current query context."""
    return [row[0] for row in query.with_entities(getattr(model, column_name)).distinct().filter(getattr(model, column_name).isnot(None)).order_by(getattr(model, column_name)).all()]

@recs_bp.route('/')
def recommendations_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 25, type=int)
    if limit not in ALLOWED_LIMITS: limit = 25
    
    sort_by = request.args.get('sort_by', 'impact')
    sort_order = request.args.get('sort_order', 'desc')
    
    active_filters = {}
    base_query = db.session.query(RecommendationInstance).join(RecommendationType).outerjoin(Resource).outerjoin(ResourceGroup).outerjoin(Subscription)
    
    filter_map = {
        'impact': (RecommendationType, 'impact'),
        'subscription_name': (Subscription, 'name'),
        'resource_group_name': (ResourceGroup, 'name'),
        'resource_type': (Resource, 'type'),
        'category': (RecommendationType, 'category')
    }

    for key, (model, col_name) in filter_map.items():
        filter_values_str = request.args.get(key)
        if filter_values_str:
            if key == 'category':
                filter_values_str = filter_values_str.replace('-', ' ')
            
            values_list = filter_values_str.split(',')
            active_filters[key] = values_list
            column = getattr(model, col_name)
            base_query = base_query.filter(func.lower(column).in_([v.lower() for v in values_list]))
        
    title_parts = []
    if active_filters.get('impact'): title_parts.append(f"{active_filters['impact'][0].title()} Impact")
    if active_filters.get('category'): title_parts.append(f"{active_filters['category'][0].title()}")
    if active_filters.get('subscription_name'): title_parts.append(f"for {active_filters['subscription_name'][0]}")
    page_title = " ".join(title_parts) + " Recommendations" if title_parts else "All Recommendations"

    sort_column_map = {
        'resource_name': Resource.name,
        'impact': RecommendationType.impact,
        'resource_type': Resource.type,
        'subscription_name': Subscription.name,
        'resource_group_name': ResourceGroup.name,
        'potential_savings': RecommendationInstance.potential_savings,
    }
    sort_column = sort_column_map.get(sort_by, RecommendationType.impact)
    
    order_logic = desc(sort_column) if sort_order == 'desc' else asc(sort_column)
    final_query = base_query.order_by(order_logic)
    
    paginated_results = final_query.paginate(page=page, per_page=limit, error_out=False)

    headers = [
        {'label': 'Resource Name', 'key': 'resource_name', 'sortable': True, 'is_link': True, 'filterable': False},
        {'label': 'Resource Type', 'key': 'resource_type', 'sortable': True, 'filterable': True},
        {'label': 'Impact', 'key': 'impact', 'sortable': True, 'filterable': True},
        {'label': 'Recommendation', 'key': 'recommendation_text', 'sortable': False, 'filterable': False},
        {'label': 'Subscription', 'key': 'subscription_name', 'sortable': True, 'filterable': True},
        {'label': 'Resource Group', 'key': 'resource_group_name', 'sortable': True, 'filterable': True},
        {'label': 'Potential Savings', 'key': 'potential_savings', 'sortable': True, 'align': 'right', 'format': 'currency', 'filterable': False},
    ]

    rows = []
    for rec in paginated_results.items:
        rows.append({
            'resource': rec.resource,
            'resource_name': rec.resource.name if rec.resource else 'N/A (Resource not imported)',
            'resource_type': rec.resource.type if rec.resource else 'N/A',
            'impact': rec.recommendation_type.impact,
            'recommendation_text': rec.recommendation_type.text,
            'subscription_name': rec.resource.resource_group.subscription.name if rec.resource else 'N/A',
            'resource_group_name': rec.resource.resource_group.name if rec.resource else 'N/A',
            'potential_savings': rec.potential_savings,
        })

    filter_data = {
        'impact': get_distinct_values(base_query, RecommendationType, 'impact'),
        'subscription_name': get_distinct_values(base_query, Subscription, 'name'),
        'resource_group_name': get_distinct_values(base_query, ResourceGroup, 'name'),
        'resource_type': get_distinct_values(base_query, Resource, 'type'),
    }

    # FIX: Dynamically build the detail route map from all service configurations and pass it to the template.
    detail_routes = {
        s['RESOURCE_TYPE']: s['DETAIL_ROUTE'] 
        for s in current_app.service_configs 
        if s.get('RESOURCE_TYPE') and s.get('DETAIL_ROUTE')
    }

    return render_template('recommendations.html', 
                           headers=headers, rows=rows, page_title=page_title,
                           filter_data=filter_data, active_filters=active_filters,
                           detail_routes=detail_routes,
                           page=page, total_pages=paginated_results.pages, total_items=paginated_results.total, 
                           limit=limit, sort_by=sort_by, sort_order=sort_order)
