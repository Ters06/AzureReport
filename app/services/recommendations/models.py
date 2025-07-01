from app.db import db
from sqlalchemy.orm import relationship

class RecommendationType(db.Model):
    """Model for the types of recommendations from Azure Advisor."""
    __tablename__ = 'recommendation_types'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, unique=True)
    category = db.Column(db.String)
    impact = db.Column(db.String)
    
    instances = relationship("RecommendationInstance", back_populates="recommendation_type", cascade="all, delete-orphan")

class RecommendationInstance(db.Model):
    """Model for specific instances of recommendations for resources."""
    __tablename__ = 'recommendation_instances'
    id = db.Column(db.Integer, primary_key=True)
    recommendation_type_id = db.Column(db.Integer, db.ForeignKey('recommendation_types.id'), nullable=False)
    
    resource_id = db.Column(db.Integer) 
    resource_type = db.Column(db.String)
    
    subscription_name = db.Column(db.String)
    resource_group_name = db.Column(db.String)
    resource_name = db.Column(db.String)
    potential_savings = db.Column(db.Float)
    
    # FIX: Add a column to store the full Azure Resource ID
    resource_uri = db.Column(db.String)

    recommendation_type = relationship("RecommendationType", back_populates="instances")
