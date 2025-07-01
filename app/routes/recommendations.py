from flask import Blueprint, render_template, request
from sqlalchemy import func
from ..models import db, RecommendationInstance, RecommendationType

recs_bp = Blueprint('recs', __name__)
ALLOWED_LIMITS = [10, 25, 50, 100]

@recs_bp.route('/recommendations')
def recommendations_list():
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

    return render_template('recommendations.html', recommendations=recs_paginated.items, 
                           page_title=page_title, page=page, 
                           total_pages=recs_paginated.pages, total_items=recs_paginated.total, limit=limit)
