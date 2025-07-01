from flask import Blueprint, render_template, request
from sqlalchemy import func
from ..models import db, VM, VMSS, RecommendationInstance, RecommendationType

vms_bp = Blueprint('vms', __name__)
ALLOWED_LIMITS = [10, 25, 50, 100]

@vms_bp.route('/vms')
def vms_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 25, type=int)
    if limit not in ALLOWED_LIMITS:
        limit = 25

    recs_subquery = db.session.query(
        RecommendationInstance.resource_id,
        func.count(RecommendationInstance.id).label('recommendation_count'),
        func.sum(RecommendationInstance.potential_savings).label('potential_savings')
    ).filter(RecommendationInstance.resource_type == 'Virtual machine').group_by(RecommendationInstance.resource_id).subquery()

    vms_query = db.session.query(
        VM,
        func.ifnull(recs_subquery.c.recommendation_count, 0).label('recommendation_count'),
        func.ifnull(recs_subquery.c.potential_savings, 0).label('potential_savings')
    ).outerjoin(recs_subquery, VM.id == recs_subquery.c.resource_id).order_by(VM.name)
    
    vms_paginated = vms_query.paginate(page=page, per_page=limit, error_out=False)
    
    vms_data = []
    for vm, rec_count, savings in vms_paginated.items:
        vms_data.append({
            'name': vm.name,
            'subscription_name': vm.resource_group.subscription.name,
            'resource_group_name': vm.resource_group.name,
            'os': vm.os,
            'size': vm.size,
            'status': vm.status,
            'recommendation_count': rec_count,
            'potential_savings': savings
        })

    return render_template('vms.html', vms=vms_data, 
                           page=page, total_pages=vms_paginated.pages, 
                           total_items=vms_paginated.total, limit=limit)

@vms_bp.route('/vm/<vm_name>')
def vm_detail(vm_name):
    vm = VM.query.filter_by(name=vm_name).first_or_404()
    recs = RecommendationInstance.query.join(RecommendationType).filter(
        RecommendationInstance.resource_type == 'Virtual machine',
        RecommendationInstance.resource_id == vm.id
    ).order_by(RecommendationType.impact).all()
    return render_template('vm_detail.html', vm=vm, recommendations=recs)

@vms_bp.route('/vmss')
def vmss_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 25, type=int)
    if limit not in ALLOWED_LIMITS:
        limit = 25

    recs_subquery = db.session.query(
        RecommendationInstance.resource_id,
        func.count(RecommendationInstance.id).label('recommendation_count'),
        func.sum(RecommendationInstance.potential_savings).label('potential_savings')
    ).filter(RecommendationInstance.resource_type == 'Virtual machine scale set').group_by(RecommendationInstance.resource_id).subquery()

    vmss_query = db.session.query(
        VMSS,
        func.ifnull(recs_subquery.c.recommendation_count, 0).label('recommendation_count'),
        func.ifnull(recs_subquery.c.potential_savings, 0).label('potential_savings')
    ).outerjoin(recs_subquery, VMSS.id == recs_subquery.c.resource_id).order_by(VMSS.name)
    
    vmss_paginated = vmss_query.paginate(page=page, per_page=limit, error_out=False)

    vmss_data = []
    for vmss_item, rec_count, savings in vmss_paginated.items:
        vmss_data.append({
            'name': vmss_item.name,
            'subscription_name': vmss_item.resource_group.subscription.name,
            'resource_group_name': vmss_item.resource_group.name,
            'os': vmss_item.os,
            'size': vmss_item.size,
            'instances': vmss_item.instances,
            'recommendation_count': rec_count,
            'potential_savings': savings
        })

    return render_template('vmss.html', vmss=vmss_data, 
                           page=page, total_pages=vmss_paginated.pages, 
                           total_items=vmss_paginated.total, limit=limit)

@vms_bp.route('/vmss/<vmss_name>')
def vmss_detail(vmss_name):
    vmss_item = VMSS.query.filter_by(name=vmss_name).first_or_404()
    recs = RecommendationInstance.query.join(RecommendationType).filter(
        RecommendationInstance.resource_type == 'Virtual machine scale set',
        RecommendationInstance.resource_id == vmss_item.id
    ).order_by(RecommendationType.impact).all()
    return render_template('vmss_detail.html', vmss=vmss_item, recommendations=recs)
