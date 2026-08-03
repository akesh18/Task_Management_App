from app.database import SessionLocal, engine, Base
from app import models
from passlib.context import CryptContext

# Database tables update/create karein
Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

# APNA ADMIN USERNAME AUR PASSWORD YAHAN SET KAREIN
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

try:
    existing_admin = db.query(models.User).filter(models.User.username == ADMIN_USER).first()
    if not existing_admin:
        hashed_pw = pwd_context.hash(ADMIN_PASS)
        admin_user = models.User(username=ADMIN_USER, hashed_password=hashed_pw, is_admin=True)
        db.add(admin_user)
        db.commit()
        print("Super Admin account created successfully!")
    else:
        print("Admin user already exists.")
except Exception as e:
    db.rollback()
    print("Database schema mismatch, recreate tasks.db file.")
finally:
    db.close()