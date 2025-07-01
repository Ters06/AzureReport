from .models import db, ClientInfo, RecommendationType

def format_currency(value):
    """Formats a value as currency."""
    if value is None or value == 0:
        return "-"
    return "${:,.2f}".format(value)

def inject_global_vars():
    """Makes global context available to all templates."""
    # It's better to handle the case where the database might be empty
    client_info = ClientInfo.query.first()
    if not client_info:
        return {
            "nav_categories": [],
            "client_name": "Azure Report",
            "report_date": "N/A"
        }

    categories_query = db.session.query(RecommendationType.category).distinct().order_by(RecommendationType.category).all()
    
    context = {
        "nav_categories": [{'category': c[0]} for c in categories_query if c[0] is not None],
        "client_name": client_info.name,
        "report_date": client_info.report_date
    }
    return context
