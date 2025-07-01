from flask import Blueprint, jsonify
from sqlalchemy import func
from ..models import db, RecommendationInstance, RecommendationType, Subscription

api_bp = Blueprint('api', __name__)

@api_bp.route('/data/recommendations-summary')
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

@api_bp.route('/data/impact-by-category/<category>')
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

@api_bp.route('/data/recommendations-by-subscription/<group_by>')
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
