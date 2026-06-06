from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.utils.config import DATABASE_URL

if not DATABASE_URL:
    # We will raise an exception if it's strictly required, 
    # but for local dev if they haven't set it yet, we just print a warning.
    print("WARNING: DATABASE_URL is not set. Database operations will fail.")

# Neon/Postgres requires the engine URL
# The `pool_pre_ping=True` checks the connection before usage, useful for cloud DBs
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
