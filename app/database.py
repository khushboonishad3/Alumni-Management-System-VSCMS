import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Configure engine depending on database dialect
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Auto-detect available PostgreSQL driver (psycopg2 -> psycopg 3 -> pure python pg8000)
if db_url.startswith("postgresql://") and not any(d in db_url for d in ["+psycopg", "+pg8000", "+asyncpg"]):
    try:
        import psycopg2
    except ImportError:
        try:
            import psycopg
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        except ImportError:
            try:
                import pg8000
                db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)
            except ImportError:
                pass

connect_args = {}
if "sqlite" in db_url:
    connect_args = {"check_same_thread": False}
    if os.getenv("VERCEL") and not db_url.startswith("sqlite:////tmp"):
        db_url = "sqlite:////tmp/cms_alumni.db"

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=False,
        pool_pre_ping=True
    )
except Exception as e:
    print(f"[DATABASE ENGINE INITIALIZATION WARNING] {e}")
    engine = create_engine("sqlite:////tmp/cms_alumni.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

