# FILE: app/services/storage_accounts/models.py
from app.db import db
from app.services.core.models import Resource

class StorageAccount(Resource):
    __tablename__ = 'storage_accounts'
    id = db.Column(db.String, db.ForeignKey('resources.id'), primary_key=True)
    sku = db.Column(db.String)
    kind = db.Column(db.String)
    __mapper_args__ = {'polymorphic_identity': 'Storage account'}