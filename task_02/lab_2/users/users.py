from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from auth import get_current_client, add_user_password, get_password_hash

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_client)],
)


# Модель данных для пользователя
class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: Optional[int] = None


class UserCreate(User):
    password: str


# Временное хранилище для пользователей
users_db: List[User] = [User(id=1, name="admin", email="admin@example.com")]


# GET /users - Получить всех пользователей
@router.get("/list", response_model=List[User])
def get_users():
    return users_db


# GET /users/{user_id} - Получить пользователя по ID
@router.get("/get", response_model=User)
def get_user(user_id: int):
    for user in users_db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")


# POST /users - Создать нового пользователя
@router.post("/create", response_model=User)
def create_user(user: UserCreate):
    for u in users_db:
        if u.id == user.id or u.email == user.email:
            raise HTTPException(status_code=404, detail="User already exist")

    hashed_password = get_password_hash(user.password)

    users_db.append(user)
    add_user_password(user.name, hashed_password)

    return User(
        id=user.id,
        name=user.name,
        email=user.email,
        age=user.age,
    )


# PUT /users/{user_id} - Обновить пользователя по ID
@router.put("/update", response_model=User)
def update_user(user_id: int, updated_user: User):
    for index, user in enumerate(users_db):
        if user.id == user_id:
            users_db[index] = updated_user
            return updated_user
    raise HTTPException(status_code=404, detail="User not found")


# DELETE /users/{user_id} - Удалить пользователя по ID
@router.delete("/delete", response_model=User)
def delete_user(user_id: int):
    for index, user in enumerate(users_db):
        if user.id == user_id:
            deleted_user = users_db.pop(index)
            return deleted_user
    raise HTTPException(status_code=404, detail="User not found")
