from app.db import db
from sqlalchemy.orm import relationship

class RecommendationType(db.Model):
    """Model for the types of recommendations from Azure Advisor."""
    __tablename__ = 'recommendation_types'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, unique=True)
    category = db.Column(db.String)
    impact = db.Column(db.String)
    
    # This relationship expects to find a 'recommendation_type' property on the RecommendationInstance model.
    instances = relationship("RecommendationInstance", back_populates="recommendation_type", cascade="all, delete-orphan")

class RecommendationInstance(db.Model):
    """Model for specific instances of recommendations for resources."""
    __tablename__ = 'recommendation_instances'
    id = db.Column(db.Integer, primary_key=True)
    recommendation_type_id = db.Column(db.Integer, db.ForeignKey('recommendation_types.id'), nullable=False)
    potential_savings = db.Column(db.Float)
    
    resource_id = db.Column(db.String, db.ForeignKey('resources.id'), nullable=True)
    resource = relationship("Resource", back_populates="recommendations")

    # FIX: Added the missing relationship back to RecommendationType.
    # This is the property that SQLAlchemy was looking for.
    recommendation_type = relationship("RecommendationType", back_populates="instances")
