from flask import Flask, render_template, request, jsonify
import sqlite3
import math
import json

app = Flask(__name__)
DATABASE = 'report.db'
ALLOWED_LIMITS = [10, 25, 50, 100]

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_global_context():
    """Fetches global data (client name, categories, report date) for the navigation bar."""
    conn = get_db_connection()
    categories = conn.execute('SELECT DISTINCT category FROM recommendation_types WHERE category IS NOT NULL ORDER BY category').fetchall()
    client_info = conn.execute('SELECT name, report_date FROM client_info WHERE id = 1').fetchone()
    conn.close()
    
    context = {
        "nav_categories": categories,
        "client_name": client_info['name'] if client_info else "Azure Report",
        "report_date": client_info['report_date'] if client_info else "N/A"
    }
    return context

@app.context_processor
def inject_global_vars():
    """Makes global context available to all templates."""
    return get_global_context()

@app.template_filter('format_currency')
def format_currency(value):
    """Formats a value as currency."""
    if value is None or value == 0:
        return "-"
    return "${:,.2f}".format(value)

@app.route('/')
def index():
    conn = get_db_connection()

    # Key Metrics
    total_recs = conn.execute('SELECT COUNT(*) FROM recommendation_instances').fetchone()[0]
    high_impact = conn.execute('SELECT COUNT(*) FROM recommendation_instances ri JOIN recommendation_types rt ON ri.recommendation_type_id = rt.id WHERE rt.impact = "High"').fetchone()[0]
    total_savings = conn.execute('SELECT SUM(potential_savings) FROM recommendation_instances').fetchone()[0]
    vm_count = conn.execute('SELECT COUNT(*) FROM vms').fetchone()[0]
    vmss_count = conn.execute('SELECT COUNT(*) FROM vmss').fetchone()[0]
    
    conn.close()

    return render_template('index.html',
                           total_recs=total_recs,
                           high_impact=high_impact,
                           total_savings=total_savings or 0,
                           vm_count=vm_count,
                           vmss_count=vmss_count)

# --- API Routes for Charts ---

@app.route('/api/data/recommendations-summary')
def recommendations_summary():
    conn = get_db_connection()
    category_data = conn.execute('SELECT rt.category, COUNT(ri.id) as count FROM recommendation_instances ri JOIN recommendation_types rt ON ri.recommendation_type_id = rt.id GROUP BY rt.category ORDER BY count DESC').fetchall()
    impact_data = conn.execute('SELECT rt.impact, COUNT(ri.id) as count FROM recommendation_instances ri JOIN recommendation_types rt ON ri.recommendation_type_id = rt.id GROUP BY rt.impact').fetchall()
    conn.close()
    
    return jsonify({
        'categories': {
            'labels': [row['category'] for row in category_data],
            'data': [row['count'] for row in category_data]
        },
        'impacts': {
            'labels': [row['impact'] for row in impact_data],
            'data': [row['count'] for row in impact_data]
        }
    })

@app.route('/api/data/impact-by-category/<category>')
def impact_by_category(category):
    conn = get_db_connection()
    formatted_category = category.replace('-', ' ')
    query = """
        SELECT rt.impact, COUNT(ri.id) as count 
        FROM recommendation_instances ri
        JOIN recommendation_types rt ON ri.recommendation_type_id = rt.id
        WHERE lower(rt.category) = lower(?)
        GROUP BY rt.impact
    """
    impact_data = conn.execute(query, (formatted_category,)).fetchall()
    conn.close()
    
    return jsonify({
        'labels': [row['impact'] for row in impact_data],
        'data': [row['count'] for row in impact_data]
    })

@app.route('/api/data/recommendations-by-subscription/<group_by>')
def recommendations_by_subscription(group_by):
    conn = get_db_connection()
    
    if group_by not in ['impact', 'category']:
        return jsonify({"error": "Invalid grouping"}), 400

    query = f"""
        SELECT 
            ri.subscription_name,
            rt.{group_by} as grouping_key,
            COUNT(ri.id) as count
        FROM recommendation_instances ri
        JOIN recommendation_types rt ON ri.recommendation_type_id = rt.id
        WHERE ri.subscription_name IS NOT NULL AND rt.{group_by} IS NOT NULL
        GROUP BY ri.subscription_name, rt.{group_by}
    """
    recs_data = conn.execute(query).fetchall()
    
    all_subs_query = "SELECT name, subscription_id_guid FROM subscriptions ORDER BY name"
    all_subs = conn.execute(all_subs_query).fetchall()
    
    all_grouping_keys_query = f"SELECT DISTINCT {group_by} FROM recommendation_types WHERE {group_by} IS NOT NULL ORDER BY {group_by}"
    all_grouping_keys = [row[0] for row in conn.execute(all_grouping_keys_query).fetchall()]
    
    conn.close()

    subs_data = {sub['name']: {'guid': sub['subscription_id_guid'], 'counts': {key: 0 for key in all_grouping_keys}} for sub in all_subs}
    
    for row in recs_data:
        sub_name = row['subscription_name']
        grouping_key = row['grouping_key']
        if sub_name in subs_data and grouping_key in subs_data[sub_name]['counts']:
            subs_data[sub_name]['counts'][grouping_key] = row['count']
            
    labels = [f"{name} ({data['guid']})" for name, data in subs_data.items()]
    datasets = {key: {"label": key, "data": []} for key in all_grouping_keys}

    for sub_name, data in subs_data.items():
        for key in all_grouping_keys:
            datasets[key]['data'].append(data['counts'].get(key, 0))
            
    return jsonify({'labels': labels, 'datasets': list(datasets.values())})


# --- Other App Routes ---

@app.route('/vms')
def vms_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 25, type=int)
    if limit not in ALLOWED_LIMITS:
        limit = 25
        
    offset = (page - 1) * limit
    
    conn = get_db_connection()
    vms_query = f"""
        SELECT
            v.name, s.name as subscription_name, rg.name as resource_group_name, v.os, v.size, v.status,
            COUNT(ri.id) as recommendation_count,
            SUM(ri.potential_savings) as potential_savings
        FROM vms v
        JOIN resource_groups rg ON v.resource_group_id = rg.id
        JOIN subscriptions s ON rg.subscription_id = s.id
        LEFT JOIN recommendation_instances ri ON v.id = ri.resource_id AND ri.resource_type = 'Virtual machine'
        GROUP BY v.id
        ORDER BY v.name
        LIMIT ? OFFSET ?
    """
    vms = conn.execute(vms_query, (limit, offset)).fetchall()
    
    total_vms = conn.execute('SELECT COUNT(*) FROM vms').fetchone()[0]
    conn.close()

    total_pages = math.ceil(total_vms / limit)
    
    return render_template('vms.html', vms=vms, page=page, total_pages=total_pages, total_items=total_vms, limit=limit)

@app.route('/vm/<vm_name>')
def vm_detail(vm_name):
    conn = get_db_connection()
    vm = conn.execute('SELECT v.*, rg.name as resource_group_name, s.name as subscription_name FROM vms v JOIN resource_groups rg ON v.resource_group_id = rg.id JOIN subscriptions s ON rg.subscription_id = s.id WHERE v.name = ?', (vm_name,)).fetchone()
    recs_query = """
        SELECT rt.*, ri.potential_savings
        FROM recommendation_instances ri
        JOIN recommendation_types rt ON ri.recommendation_type_id = rt.id
        WHERE ri.resource_id = ? AND ri.resource_type = 'Virtual machine'
        ORDER BY rt.impact
    """
    recs = conn.execute(recs_query, (vm['id'],)).fetchall()
    conn.close()
    return render_template('vm_detail.html', vm=vm, recommendations=recs)

@app.route('/vmss')
def vmss_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 25, type=int)
    if limit not in ALLOWED_LIMITS:
        limit = 25

    offset = (page - 1) * limit
    
    conn = get_db_connection()
    vmss_query = f"""
        SELECT
            vs.name, s.name as subscription_name, rg.name as resource_group_name, vs.os, vs.size, vs.instances,
            COUNT(ri.id) as recommendation_count,
            SUM(ri.potential_savings) as potential_savings
        FROM vmss vs
        JOIN resource_groups rg ON vs.resource_group_id = rg.id
        JOIN subscriptions s ON rg.subscription_id = s.id
        LEFT JOIN recommendation_instances ri ON vs.id = ri.resource_id AND ri.resource_type = 'Virtual machine scale set'
        GROUP BY vs.id
        ORDER BY vs.name
        LIMIT ? OFFSET ?
    """
    vmss = conn.execute(vmss_query, (limit, offset)).fetchall()
    total_vmss = conn.execute('SELECT COUNT(*) FROM vmss').fetchone()[0]
    conn.close()

    total_pages = math.ceil(total_vmss / limit)

    return render_template('vmss.html', vmss=vmss, page=page, total_pages=total_pages, total_items=total_vmss, limit=limit)

@app.route('/vmss/<vmss_name>')
def vmss_detail(vmss_name):
    conn = get_db_connection()
    vmss_item = conn.execute('SELECT vs.*, rg.name as resource_group_name, s.name as subscription_name FROM vmss vs JOIN resource_groups rg ON vs.resource_group_id = rg.id JOIN subscriptions s ON rg.subscription_id = s.id WHERE vs.name = ?', (vmss_name,)).fetchone()
    recs_query = """
        SELECT rt.*, ri.potential_savings
        FROM recommendation_instances ri
        JOIN recommendation_types rt ON ri.recommendation_type_id = rt.id
        WHERE ri.resource_id = ? AND ri.resource_type = 'Virtual machine scale set'
        ORDER BY rt.impact
    """
    recs = conn.execute(recs_query, (vmss_item['id'],)).fetchall()
    conn.close()
    return render_template('vmss_detail.html', vmss=vmss_item, recommendations=recs)

@app.route('/recommendations')
def recommendations_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 25, type=int)
    if limit not in ALLOWED_LIMITS:
        limit = 25
    
    offset = (page - 1) * limit
    
    conn = get_db_connection()
    category = request.args.get('category', None)
    impact = request.args.get('impact', None)
    subscription = request.args.get('subscription', None)
    
    base_query = "FROM recommendation_instances ri JOIN recommendation_types rt ON ri.recommendation_type_id = rt.id"
    params = []
    conditions = []
    
    title_parts = []
    if impact:
        conditions.append("lower(rt.impact) = lower(?)")
        params.append(impact)
        title_parts.append(f"{impact.title()} Impact")
    
    if category:
        conditions.append("lower(rt.category) = lower(?)")
        params.append(category.replace('-', ' '))
        title_parts.append(f"{category.replace('-', ' ').title()}")

    if subscription:
        conditions.append("ri.subscription_name = ?")
        params.append(subscription)
        title_parts.append(f"for {subscription}")
    
    page_title = " ".join(title_parts) + " Recommendations" if title_parts else "All Recommendations"

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    count_query = "SELECT COUNT(*) " + base_query + where_clause
    total_recs = conn.execute(count_query, params).fetchone()[0]
    
    data_query = "SELECT ri.*, rt.text as recommendation_text, rt.impact, rt.category " + base_query + where_clause + " ORDER BY rt.impact DESC, ri.resource_name LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    recs = conn.execute(data_query, params).fetchall()
    
    conn.close()
    
    total_pages = math.ceil(total_recs / limit)

    return render_template('recommendations.html', recommendations=recs, page_title=page_title, page=page, total_pages=total_pages, total_items=total_recs, limit=limit)

if __name__ == '__main__':
    app.run(debug=True)
