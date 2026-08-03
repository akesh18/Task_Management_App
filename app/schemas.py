from pydantic import BaseModel
from typing import Optional, List

# --- JWT Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- User Schemas ---
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool = False

    class Config:
        from_attributes = True

# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class TaskResponse(TaskBase):
    id: int
    completed: bool
    owner_id: int

    class Config:
        from_attributes = True

# --- Admin Overview Schema ---
class AdminUserOverview(BaseModel):
    id: int
    username: str
    is_admin: bool
    task_count: int
    tasks: List[TaskResponse]

    class Config:
        from_attributes = True