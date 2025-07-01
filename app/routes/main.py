from flask import Blueprint, render_template
from sqlalchemy import func
from ..models import db, RecommendationInstance, RecommendationType, VM, VMSS, StorageAccount

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Dashboard route."""
    total_recs = db.session.query(func.count(RecommendationInstance.id)).scalar()
    high_impact = RecommendationInstance.query.join(RecommendationType).filter(RecommendationType.impact == 'High').count()
    total_savings = db.session.query(func.sum(RecommendationInstance.potential_savings)).scalar()
    vm_count = VM.query.count()
    vmss_count = VMSS.query.count()
    storage_count = StorageAccount.query.count() # New KPI

    return render_template('index.html',
                           total_recs=total_recs,
                           high_impact=high_impact,
                           total_savings=total_savings or 0,
                           vm_count=vm_count,
                           vmss_count=vmss_count,
                           storage_count=storage_count) # Pass new KPI to template
