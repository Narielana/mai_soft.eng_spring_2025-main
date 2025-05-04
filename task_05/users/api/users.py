from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
import json
import redis.asyncio
import os

from api.auth import get_current_client, get_password_hash
from database.database import get_db
from database import models

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.asyncio.from_url(redis_url, encoding="utf-8", decode_responses=True)

async def get_redis():
    return redis_client

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

# GET /users/list - Получить всех пользователей
@router.get("/list", response_model=ListResponse)
async def get_users(
    username: Optional[str] = None, 
    name: Optional[str] = None, 
    surname: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    redis: redis.asyncio.Redis = Depends(get_redis)
):
    cache_key = f"users:list:{username}:{name}:{surname}:{limit}:{offset}"
    
    cached_data = await redis.get(cache_key)
    if cached_data:
        cached_list = json.loads(cached_data)
        return ListResponse(
            users=[User(**user) for user in cached_list["users"]],
            limit=cached_list["limit"],
            offset=cached_list["offset"]
        )
    
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
    
    response = ListResponse(
        users=users,
        limit=limit,
        offset=offset+limit,
    )
    
    users_dict = [
        {
            "id": user.id,
            "name": user.name,
            "surname": user.surname, 
            "email": user.email,
            "age": user.age,
            "username": user.username
        } 
        for user in users
    ]
    
    cache_data = {
        "users": users_dict,
        "limit": limit,
        "offset": offset+limit
    }
    
    await redis.set(cache_key, json.dumps(cache_data), ex=300)
    
    return response

# GET /users/list-no-cache - Получить всех пользователей (без кеша)
@router.get("/list-no-cache", response_model=ListResponse)
async def get_users_no_cache(
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

# GET /users/get - Получить пользователя по ID
@router.get("/get", response_model=User)
async def get_user(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    redis: redis.asyncio.Redis = Depends(get_redis)
):
    cache_key = f"users:get:{user_id}"
    cached_user = await redis.get(cache_key)
    
    if cached_user:
        user_data = json.loads(cached_user)
        return User(**user_data)
    
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = {
        "id": user.id,
        "name": user.name,
        "surname": user.surname,
        "email": user.email,
        "age": user.age,
        "username": user.username
    }
    await redis.set(cache_key, json.dumps(user_data), ex=300)
    
    return user

# GET /users/get-no-cache - Получить пользователя по ID (без кеша)
@router.get("/get-no-cache", response_model=User)
async def get_user_no_cache(
    user_id: int, 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# POST /users/create - Создать нового пользователя
@router.post("/create", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate, 
    db: AsyncSession = Depends(get_db),
    redis: redis.asyncio.Redis = Depends(get_redis)
):
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
    
    keys_to_delete = []
    async for key in redis.scan_iter("users:list:*"):
        keys_to_delete.append(key)
    
    if keys_to_delete:
        await redis.delete(*keys_to_delete)
    
    user_data = {
        "id": db_user.id,
        "name": db_user.name,
        "surname": db_user.surname,
        "email": db_user.email,
        "age": db_user.age,
        "username": db_user.username
    }
    await redis.set(f"users:get:{db_user.id}", json.dumps(user_data), ex=300)
    
    return db_user

# PUT /users/update - Обновить пользователя по ID
@router.put("/update", response_model=User)
async def update_user(
    user_id: int, 
    user_data: UserBase, 
    db: AsyncSession = Depends(get_db),
    redis: redis.asyncio.Redis = Depends(get_redis)
):
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
        
        await redis.delete(f"users:get:{user_id}")
        
        keys_to_delete = []
        async for key in redis.scan_iter("users:list:*"):
            keys_to_delete.append(key)
        
        if keys_to_delete:
            await redis.delete(*keys_to_delete)
        
        updated_user = {
            "id": db_user.id,
            "name": db_user.name,
            "surname": db_user.surname,
            "email": db_user.email,
            "age": db_user.age,
            "username": db_user.username
        }
        await redis.set(f"users:get:{user_id}", json.dumps(updated_user), ex=300)
        
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail='Username or email already exists'
        )
    return db_user

# DELETE /users/delete - Удалить пользователя по ID
@router.delete("/delete", response_model=User)
async def delete_user(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    redis: redis.asyncio.Redis = Depends(get_redis)
):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = User(
        id=db_user.id,
        name=db_user.name,
        surname=db_user.surname,
        email=db_user.email,
        age=db_user.age,
        username=db_user.username
    )
    
    await db.delete(db_user)
    await db.commit()
    
    await redis.delete(f"users:get:{user_id}")
    
    keys_to_delete = []
    async for key in redis.scan_iter("users:list:*"):
        keys_to_delete.append(key)
    
    if keys_to_delete:
        await redis.delete(*keys_to_delete)
    
    return user_data
