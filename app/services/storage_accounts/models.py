from app.db import db
from app.services.core.models import ResourceGroup
from sqlalchemy.orm import relationship

class StorageAccount(db.Model):
    """Model for Azure Storage Accounts."""
    __tablename__ = 'storage_accounts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    location = db.Column(db.String)
    sku = db.Column(db.String)
    kind = db.Column(db.String)
    resource_group_id = db.Column(db.Integer, db.ForeignKey('resource_groups.id'), nullable=False)
    
    resource_group = relationship("ResourceGroup")