# FILE: app/services/virtual_machines/models.py
from app.db import db
from app.services.core.models import Resource

class VM(Resource):
    __tablename__ = 'vms'
    id = db.Column(db.String, db.ForeignKey('resources.id'), primary_key=True)
    status = db.Column(db.String)
    os = db.Column(db.String)
    size = db.Column(db.String)
    public_ip = db.Column(db.String)
    disks = db.Column(db.Integer)
    __mapper_args__ = {'polymorphic_identity': 'Virtual machine'}