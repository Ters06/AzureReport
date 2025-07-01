# This file holds the shared SQLAlchemy database instance,
# preventing circular import errors.
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()