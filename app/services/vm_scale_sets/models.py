# FILE: app/services/vm_scale_sets/models.py
from app.db import db
from app.services.core.models import Resource

class VMSS(Resource):
    __tablename__ = 'vmss'
    id = db.Column(db.String, db.ForeignKey('resources.id'), primary_key=True)
    status = db.Column(db.String)
    os = db.Column(db.String)
    size = db.Column(db.String)
    instances = db.Column(db.Integer)
    __mapper_args__ = {'polymorphic_identity': 'Virtual machine scale set'}