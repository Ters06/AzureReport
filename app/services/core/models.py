from app.db import db
from sqlalchemy.orm import relationship

class ClientInfo(db.Model):
    __tablename__ = 'client_info'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    report_date = db.Column(db.String)

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    resource_groups = relationship("ResourceGroup", back_populates="subscription", cascade="all, delete-orphan")

class ResourceGroup(db.Model):
    __tablename__ = 'resource_groups'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    subscription_id = db.Column(db.String, db.ForeignKey('subscriptions.id'), nullable=False)
    subscription = relationship("Subscription", back_populates="resource_groups")
    resources = relationship("Resource", back_populates="resource_group", cascade="all, delete-orphan")

class Resource(db.Model):
    __tablename__ = 'resources'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)
    location = db.Column(db.String)
    resource_group_id = db.Column(db.String, db.ForeignKey('resource_groups.id'), nullable=False)
    resource_group = relationship("ResourceGroup", back_populates="resources")
    recommendations = relationship("RecommendationInstance", back_populates="resource", cascade="all, delete-orphan")
    __mapper_args__ = {'polymorphic_on': type, 'polymorphic_identity': 'resource'}
