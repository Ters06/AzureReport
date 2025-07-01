from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class ClientInfo(db.Model):
    __tablename__ = 'client_info'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    report_date = db.Column(db.String)

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    subscription_id_guid = db.Column(db.String, unique=True, nullable=False)
    
    resource_groups = relationship("ResourceGroup", back_populates="subscription", cascade="all, delete-orphan")

class ResourceGroup(db.Model):
    __tablename__ = 'resource_groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    
    subscription = relationship("Subscription", back_populates="resource_groups")
    vms = relationship("VM", back_populates="resource_group", cascade="all, delete-orphan")
    vmss = relationship("VMSS", back_populates="resource_group", cascade="all, delete-orphan")
    # Add relationship to Storage Accounts
    storage_accounts = relationship("StorageAccount", back_populates="resource_group", cascade="all, delete-orphan")
    
    __table_args__ = (db.UniqueConstraint('name', 'subscription_id', name='_subscription_rg_uc'),)

class VM(db.Model):
    __tablename__ = 'vms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    location = db.Column(db.String)
    status = db.Column(db.String)
    os = db.Column(db.String)
    size = db.Column(db.String)
    public_ip = db.Column(db.String)
    disks = db.Column(db.Integer)
    resource_group_id = db.Column(db.Integer, db.ForeignKey('resource_groups.id'), nullable=False)
    
    resource_group = relationship("ResourceGroup", back_populates="vms")

class VMSS(db.Model):
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
    
    resource_group = relationship("ResourceGroup", back_populates="vmss")

# New Model for Storage Accounts
class StorageAccount(db.Model):
    __tablename__ = 'storage_accounts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    location = db.Column(db.String)
    sku = db.Column(db.String)
    kind = db.Column(db.String)
    resource_group_id = db.Column(db.Integer, db.ForeignKey('resource_groups.id'), nullable=False)
    
    resource_group = relationship("ResourceGroup", back_populates="storage_accounts")

class RecommendationType(db.Model):
    __tablename__ = 'recommendation_types'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, unique=True)
    category = db.Column(db.String)
    impact = db.Column(db.String)
    
    instances = relationship("RecommendationInstance", back_populates="recommendation_type", cascade="all, delete-orphan")

class RecommendationInstance(db.Model):
    __tablename__ = 'recommendation_instances'
    id = db.Column(db.Integer, primary_key=True)
    recommendation_type_id = db.Column(db.Integer, db.ForeignKey('recommendation_types.id'), nullable=False)
    
    resource_id = db.Column(db.Integer) 
    resource_type = db.Column(db.String)
    
    subscription_name = db.Column(db.String)
    resource_group_name = db.Column(db.String)
    resource_name = db.Column(db.String)
    potential_savings = db.Column(db.Float)
    
    recommendation_type = relationship("RecommendationType", back_populates="instances")
