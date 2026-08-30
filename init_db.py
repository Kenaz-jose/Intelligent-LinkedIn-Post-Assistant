from src.db.base import engine
from src.db.models import Base

print("Building database schema...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully!")