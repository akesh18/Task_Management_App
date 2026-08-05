from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from app import database, models, schemas

SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# ================= SIGNUP ROUTE =================
@router.post("/signup")
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    if user.username.lower() == "admin":
        raise HTTPException(
            status_code=400, 
            detail="Username already exists, please choose another username"
        )
        
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail="Username already exists, please choose another username"
        )
        
    hashed_pw = pwd_context.hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_pw, is_admin=False)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

# ================= LOGIN ROUTE =================
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    login_role = form_data.client_id or "user"

    if not user:
        raise HTTPException(
            status_code=404, 
            detail="Username not registered, please create new account"
        )
        
    if login_role == "user" and user.is_admin:
        raise HTTPException(
            status_code=403, 
            detail="Admin account cannot be logged in from User login page."
        )
        
    if login_role == "admin" and not user.is_admin:
        raise HTTPException(
            status_code=403, 
            detail="You are not authorized to login as Admin."
        )

    if not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401, 
            detail="The password you've entered is incorrect. Please enter correct password"
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ================= ADMIN OVERVIEW ROUTE =================
@router.get("/admin/users-overview")
def get_admin_overview(
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    users = db.query(models.User).all()
    overview = []
    for u in users:
        task_count = db.query(models.Task).filter(models.Task.owner_id == u.id).count()
        overview.append({
            "id": u.id,
            "username": u.username,
            "is_admin": u.is_admin,
            "task_count": task_count
        })
    return overview

# ================= DELETE ROUTES =================
@router.delete("/users/me")
def delete_own_account(
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    db.query(models.Task).filter(models.Task.owner_id == current_user.id).delete()
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}

@router.delete("/admin/users/{user_id}")
def delete_user_by_admin(
    user_id: int, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user_to_delete.is_admin:
        raise HTTPException(status_code=400, detail="Cannot delete Super Admin")
        
    db.query(models.Task).filter(models.Task.owner_id == user_id).delete()
    db.delete(user_to_delete)
    db.commit()
    return {"message": f"User {user_to_delete.username} deleted"}