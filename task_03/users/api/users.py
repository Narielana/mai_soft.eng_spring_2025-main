from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from api.auth import get_current_client, get_password_hash
from database.database import get_db
from database import models


class UserBase(BaseModel):
    name: str
    surname: str
    email: EmailStr
    age: Optional[int] = None


class UserCreate(UserBase):
    username: str
    password: str


class User(UserBase):
    id: int
    username: str
    
    class Config:
        from_attributes = True


class ListResponse(BaseModel):
    users: List[User]
    limit: int
    offset: int


router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_client)],
)


# GET /users - Получить всех пользователей
@router.get("/list", response_model=ListResponse)
async def get_users(
    username: Optional[str] = None, 
    name: Optional[str] = None, 
    surname: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    query = select(models.User)

    filters = []
    
    if username:
        filters.append(models.User.username == username)

    if name:
        filters.append(models.User.name == name)
    
    if surname:
        filters.append(models.User.surname == surname)

    if filters:
        query = query.filter(and_(*filters))

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    users = result.scalars().all()

    return ListResponse(
        users=users,
        limit=limit,
        offset=offset+limit,
    )


# GET /users/{user_id} - Получить пользователя по ID
@router.get("/get", response_model=User)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# POST /users - Создать нового пользователя
@router.post("/create", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.User).filter(
            (models.User.email == user_data.email) | 
            (models.User.username == user_data.username)
        )
    )
    existing_user = result.scalars().first()
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        else:
            raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = get_password_hash(user_data.password)
    db_user = models.User(
        name=user_data.name,
        surname=user_data.surname,
        email=user_data.email,
        age=user_data.age,
        username=user_data.username,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user


# PUT /users/{user_id} - Обновить пользователя по ID
@router.put("/update", response_model=User)
async def update_user(user_id: int, user_data: UserBase, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.name = user_data.name
    db_user.surname = user_data.surname
    db_user.email = user_data.email
    db_user.age = user_data.age
    try:
        await db.commit()
        await db.refresh(db_user)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail='Username or email already exists'
        )
    return db_user


# DELETE /users/{user_id} - Удалить пользователя по ID
@router.delete("/delete", response_model=User)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(db_user)
    await db.commit()
    return db_user
