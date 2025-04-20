from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum
from pymongo import MongoClient, ReturnDocument
from bson import ObjectId
import os

from auth import get_current_user


# Конфигурация MongoDB
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://stud:stud@mongo:27017/delivery_db")
client = MongoClient(MONGO_URI)
db = client.get_database()
delivery_collection = db.deliveries


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELED = "canceled"


# Совместимый с Pydantic способ работы с ObjectId
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, (str, ObjectId)):
            raise TypeError('ObjectId required')
        return str(v)


class DeliveryBase(BaseModel):
    description: str
    address: str
    contact_phone: str
    delivery_time: Optional[datetime] = None


class DeliveryCreate(DeliveryBase):
    pass


class Delivery(DeliveryBase):
    id: str = Field(alias="_id")
    status: DeliveryStatus = DeliveryStatus.PENDING
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: int  # ID пользователя, создавшего доставку
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }


class DeliveryUpdate(BaseModel):
    description: Optional[str] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    delivery_time: Optional[datetime] = None
    status: Optional[DeliveryStatus] = None


class DeliveryStatusUpdate(BaseModel):
    status: DeliveryStatus


router = APIRouter(
    prefix="/deliveries",
    tags=["deliveries"],
)


def serialize_object_id(obj):
    """Преобразует ObjectId в строки для JSON сериализации"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, ObjectId):
                obj[k] = str(v)
            elif isinstance(v, (dict, list)):
                obj[k] = serialize_object_id(v)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, ObjectId):
                obj[i] = str(v)
            elif isinstance(v, (dict, list)):
                obj[i] = serialize_object_id(v)
    return obj


@router.post("/create", response_model=Delivery, status_code=status.HTTP_201_CREATED)
async def create_delivery(
    delivery: DeliveryCreate, 
    user_id: int = Depends(get_current_user)
):
    """Создать новую доставку"""
    now = datetime.now()
    
    new_delivery = {
        **delivery.dict(),
        "status": DeliveryStatus.PENDING,
        "created_at": now,
        "updated_at": None,
        "user_id": user_id,
    }
    
    result = delivery_collection.insert_one(new_delivery)
    created_delivery = delivery_collection.find_one({"_id": result.inserted_id})
    
    return serialize_object_id(created_delivery)


@router.get("/list", response_model=List[Delivery])
async def list_deliveries(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[DeliveryStatus] = None,
    user_id: int = Depends(get_current_user)
):
    filter_query = {}
    if status:
        filter_query["status"] = status
    
    deliveries = list(delivery_collection.find(filter_query).skip(skip).limit(limit))
    return serialize_object_id(deliveries)


@router.get("/details", response_model=Delivery)
async def get_delivery(
    delivery_id: str, 
    user_id: int = Depends(get_current_user)
):
    try:
        delivery = delivery_collection.find_one({"_id": ObjectId(delivery_id)})
        if delivery:
            return serialize_object_id(delivery)
    except:
        pass
    
    raise HTTPException(status_code=404, detail="Delivery not found")


@router.put("/update", response_model=Delivery)
async def update_delivery(
    delivery_id: str,
    delivery_update: DeliveryUpdate, 
    user_id: int = Depends(get_current_user)
):
    try:
        update_data = {k: v for k, v in delivery_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=400, 
                detail="At least one field must be updated"
            )

        update_data["updated_at"] = datetime.now()
        
        delivery = delivery_collection.find_one_and_update(
            {"_id": ObjectId(delivery_id)},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        
        if delivery:
            return serialize_object_id(delivery)
    except:
        pass
    
    raise HTTPException(status_code=404, detail="Delivery not found")


@router.delete("/delete", response_model=Delivery)
async def delete_delivery(
    delivery_id: str, 
    user_id: int = Depends(get_current_user)
):
    try:
        delivery = delivery_collection.find_one_and_delete({"_id": ObjectId(delivery_id)})
        if delivery:
            return serialize_object_id(delivery)
    except:
        pass
    
    raise HTTPException(status_code=404, detail="Delivery not found")


@router.patch("/update_status", response_model=Delivery)
async def update_delivery_status(
    delivery_id: str,
    status_update: DeliveryStatusUpdate, 
    user_id: int = Depends(get_current_user)
):
    try:
        delivery = delivery_collection.find_one_and_update(
            {"_id": ObjectId(delivery_id)},
            {"$set": {
                "status": status_update.status,
                "updated_at": datetime.now()
            }},
            return_document=ReturnDocument.AFTER
        )
        
        if delivery:
            return serialize_object_id(delivery)
    except:
        pass
    
    raise HTTPException(status_code=404, detail="Delivery not found")
