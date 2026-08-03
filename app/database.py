from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL (Project folder ke andar 'tasks.db' naam se file banegi)
SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"

# Engine create kar rahe hain (SQLite ke liye check_same_thread False hota hai)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Database Session create karne ke liye
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base Class jisse hamare models inherit karenge
Base = declarative_base()

# Database Dependency (Har request me DB session manage karega)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()