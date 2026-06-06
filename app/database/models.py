from sqlalchemy import Column, Integer, String, Text, DateTime, Date, func
from sqlalchemy.sql import text
from app.database.connection import Base, engine

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)
    title = Column(String, nullable=False)
    link = Column(String, unique=True, nullable=False)
    content = Column(Text)
    category = Column(String)
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, server_default=func.now())

class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    summary_date = Column(Date, nullable=False)
    topic = Column(String, default="General", nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class Trend(Base):
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    score = Column(Integer)
    reasoning = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    category = Column(String)
    link = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

def init_db():
    """Create all tables if they don't exist yet."""
    if engine:
        Base.metadata.create_all(bind=engine)
        
        # Safely attempt to add the 'topic' column to existing DBs if it doesn't exist
        with engine.begin() as conn:
            try:
                conn.execute(text("ALTER TABLE summaries ADD COLUMN topic TEXT DEFAULT 'General';"))
                print("Added 'topic' column to summaries table.")
            except Exception:
                # Column likely already exists
                pass
    else:
        print("Cannot initialize database: DATABASE_URL is not set.")

if __name__ == "__main__":
    init_db()
    print("Database tables initialized successfully.")
