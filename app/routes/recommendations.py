from flask import Blueprint, render_template, request
from sqlalchemy import func, desc, asc
from ..models import db, RecommendationInstance, RecommendationType

recs_bp = Blueprint('recs', __name__)
ALLOWED_LIMITS = [10, 25, 50, 100]

def get_distinct_rec_values(column_name):
    """Helper for recommendation instances."""
    return [row[0] for row in db.session.query(getattr(RecommendationInstance, column_name)).distinct().filter(getattr(RecommendationInstance, column_name).isnot(None)).order_by(getattr(RecommendationInstance, column_name)).all()]

def get_distinct_rec_type_values(column_name):
    """Helper for recommendation types."""
    return [row[0] for row in db.session.query(getattr(RecommendationType, column_name)).distinct().filter(getattr(RecommendationType, column_name).isnot(None)).order_by(getattr(RecommendationType, column_name)).all()]

@recs_bp.route('/recommendations')
def recommendations_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 25, type=int)
    if limit not in ALLOWED_LIMITS: limit = 25
    
    sort_by = request.args.get('sort_by', 'impact')
    sort_order = request.args.get('sort_order', 'desc')
    
    active_filters = {}
    query = RecommendationInstance.query.join(RecommendationType)
    
    # --- Unified Filtering Logic ---
    filter_map = {
        'impact': (RecommendationType, 'impact'),
        'subscription_name': (RecommendationInstance, 'subscription_name'),
        'category': (RecommendationType, 'category')
    }

    for key, (model, col_name) in filter_map.items():
        filter_values_str = request.args.get(key)
        if filter_values_str:
            # Special handling for category from nav dropdowns which use hyphens
            if key == 'category':
                filter_values_str = filter_values_str.replace('-', ' ')
            
            values_list = filter_values_str.split(',')
            active_filters[key] = values_list
            
            # Apply a case-insensitive filter for robustness
            column = getattr(model, col_name)
            query = query.filter(func.lower(column).in_([v.lower() for v in values_list]))
        
    # Build page title based on active filters
    title_parts = []
    if active_filters.get('impact'): title_parts.append(f"{active_filters['impact'][0].title()} Impact")
    if active_filters.get('category'): title_parts.append(f"{active_filters['category'][0].title()}")
    if active_filters.get('subscription_name'): title_parts.append(f"for {active_filters['subscription_name'][0]}")
    page_title = " ".join(title_parts) + " Recommendations" if title_parts else "All Recommendations"

    # --- Sorting Logic ---
    sort_column_map = {
        'resource_name': RecommendationInstance.resource_name,
        'impact': RecommendationType.impact,
        'potential_savings': RecommendationInstance.potential_savings
    }
    sort_column = sort_column_map.get(sort_by, RecommendationType.impact)
    
    order_logic = desc(sort_column) if sort_order == 'desc' else asc(sort_column)
    query = query.order_by(order_logic)
    
    paginated_results = query.paginate(page=page, per_page=limit, error_out=False)

    # --- Data for Template ---
    headers = [
        {'label': 'Resource Name', 'key': 'resource_name', 'sortable': True, 'is_link': True, 'filterable': False},
        {'label': 'Impact', 'key': 'impact', 'sortable': True, 'filterable': True},
        {'label': 'Recommendation', 'key': 'recommendation_text', 'sortable': False, 'filterable': False},
        {'label': 'Subscription', 'key': 'subscription_name', 'sortable': False, 'filterable': True},
        {'label': 'Potential Savings', 'key': 'potential_savings', 'sortable': True, 'align': 'right', 'format': 'currency', 'filterable': False},
    ]

    rows = []
    for rec in paginated_results.items:
        rows.append({
            'resource_name': rec.resource_name,
            'impact': rec.recommendation_type.impact,
            'recommendation_text': rec.recommendation_type.text,
            'subscription_name': rec.subscription_name,
            'potential_savings': rec.potential_savings,
            'resource_type': rec.resource_type,
            'resource_id': rec.resource_id
        })

    filter_data = {
        'impact': get_distinct_rec_type_values('impact'),
        'subscription_name': get_distinct_rec_values('subscription_name')
    }

    return render_template('recommendations.html', 
                           headers=headers, rows=rows, page_title=page_title,
                           filter_data=filter_data, active_filters=active_filters,
                           page=page, total_pages=paginated_results.pages, total_items=paginated_results.total, 
                           limit=limit, sort_by=sort_by, sort_order=sort_order)
