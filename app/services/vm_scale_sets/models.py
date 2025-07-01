from app.db import db
from app.services.core.models import ResourceGroup
from sqlalchemy.orm import relationship

class VMSS(db.Model):
    """Model for Azure Virtual Machine Scale Sets."""
    __tablename__ = 'vmss'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    location = db.Column(db.String)
    provisioning_state = db.Column(db.String)
    status = db.Column(db.String)
    os = db.Column(db.String)
    size = db.Column(db.String)
    instances = db.Column(db.Integer)
    orchestration_mode = db.Column(db.String)
    public_ip = db.Column(db.String)
    resource_group_id = db.Column(db.Integer, db.ForeignKey('resource_groups.id'), nullable=False)
    
    resource_group = relationship("ResourceGroup")