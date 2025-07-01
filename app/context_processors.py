from flask import current_app
from app.db import db
from app.services.core.models import ClientInfo
from app.services.recommendations.models import RecommendationType

def format_currency(value):
    """Formats a value as currency."""
    if value is None or value == 0:
        return "-"
    return "${:,.2f}".format(value)

def inject_global_vars():
    """Makes global context available to all templates."""
    client_info = ClientInfo.query.first()
    
    # Get service configs from the application object to avoid circular imports
    all_services = current_app.service_configs
    nav_services = sorted(
        [s for s in all_services if s.get('SHOW_IN_NAV')],
        key=lambda x: x.get('NAV_ORDER', 99)
    )

    if not client_info:
        categories_query = []
    else:
        categories_query = db.session.query(RecommendationType.category).distinct().order_by(RecommendationType.category).all()
    
    context = {
        "nav_categories": [{'category': c[0]} for c in categories_query if c[0] is not None],
        "client_name": client_info.name if client_info else "Azure Report",
        "report_date": client_info.report_date if client_info else "N/A",
        "nav_services": nav_services
    }
    return context
