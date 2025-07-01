from flask import Blueprint, render_template, current_app, request, url_for
from sqlalchemy import func
from app.db import db
from app.services.core.models import Resource
from app.services.recommendations.models import RecommendationInstance, RecommendationType
import importlib

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Dashboard route."""
    total_recs = db.session.query(func.count(RecommendationInstance.id)).scalar()
    high_impact = RecommendationInstance.query.join(RecommendationType).filter(RecommendationType.impact == 'High').count()
    total_savings = db.session.query(func.sum(RecommendationInstance.potential_savings)).scalar()
    
    service_configs = current_app.service_configs
    service_counts = {}
    for config in service_configs:
        if config.get('SHOW_IN_NAV'):
            resource_type = config.get('RESOURCE_TYPE')
            if resource_type:
                count = Resource.query.filter_by(type=resource_type).count()
                service_counts[config['KEY']] = count

    return render_template('index.html',
                           total_recs=total_recs,
                           high_impact=high_impact,
                           total_savings=total_savings or 0,
                           service_counts=service_counts)

@main_bp.route('/search')
def search():
    query = request.args.get('q', '')
    results = []
    if query:
        search_term = f"%{query}%"
        
        found_resources = Resource.query.filter(Resource.name.ilike(search_term)).all()
        
        service_configs = current_app.service_configs
        route_map = {s['RESOURCE_TYPE']: s['DETAIL_ROUTE'] for s in service_configs if s.get('RESOURCE_TYPE') and s.get('DETAIL_ROUTE')}

        for resource in found_resources:
            detail_route = route_map.get(resource.type)
            if detail_route:
                results.append({
                    'name': resource.name, 
                    'type': resource.type, 
                    'url': url_for(detail_route, resource_id=resource.id)
                })
            
    return render_template('search_results.html', query=query, results=results)
