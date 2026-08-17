import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from app.models import Base

print("Recreating database tables directly using SQLAlchemy...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")
