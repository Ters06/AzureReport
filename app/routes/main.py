from flask import Blueprint, render_template, current_app, request, url_for
from sqlalchemy import func, or_
from app.db import db
from app.services.recommendations.models import RecommendationInstance, RecommendationType
from app.services.virtual_machines.models import VM
from app.services.vm_scale_sets.models import VMSS
from app.services.storage_accounts.models import StorageAccount
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
        if config.get('SHOW_IN_NAV') and 'MODEL_MODULES' in config and 'MODEL_CLASS_NAME' in config:
            model_module_path = config['MODEL_MODULES'][0]
            model_name = config['MODEL_CLASS_NAME']
            
            try:
                module = importlib.import_module(model_module_path, package='app')
                model = getattr(module, model_name)
                count = model.query.count()
                service_counts[config['KEY']] = count
            except (ImportError, AttributeError) as e:
                print(f"Could not load model for service KPI {config['KEY']}: {e}")
                service_counts[config['KEY']] = 0

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
        
        vms = VM.query.filter(VM.name.ilike(search_term)).all()
        for vm in vms:
            results.append({'name': vm.name, 'type': 'Virtual Machine', 'url': url_for('vms.vm_detail', resource_name=vm.name)})

        vmss_items = VMSS.query.filter(VMSS.name.ilike(search_term)).all()
        for item in vmss_items:
            results.append({'name': item.name, 'type': 'VM Scale Set', 'url': url_for('vmss.vmss_detail', resource_name=item.name)})

        storage_items = StorageAccount.query.filter(StorageAccount.name.ilike(search_term)).all()
        for item in storage_items:
            results.append({'name': item.name, 'type': 'Storage Account', 'url': url_for('storage.storage_account_detail', resource_name=item.name)})
            
    return render_template('search_results.html', query=query, results=results)
