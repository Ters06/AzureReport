from app.db import db
from sqlalchemy.orm import relationship

# These are the foundational models that other services depend on.

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
    __table_args__ = (db.UniqueConstraint('name', 'subscription_id', name='_subscription_rg_uc'),)