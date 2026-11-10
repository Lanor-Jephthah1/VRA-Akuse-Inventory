import os
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

IS_VERCEL = bool(os.environ.get("VERCEL"))

if IS_VERCEL:
    # On Vercel serverless, /var/task is read-only. We copy the bundled seeded database to /tmp
    DB_PATH = "/tmp/vra_akuse_inventory.db"
    SOURCE_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vra_akuse_inventory.db")
    if not os.path.exists(DB_PATH) and os.path.exists(SOURCE_DB):
        shutil.copy2(SOURCE_DB, DB_PATH)
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./vra_akuse_inventory.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
