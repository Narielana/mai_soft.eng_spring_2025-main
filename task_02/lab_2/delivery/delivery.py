from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime
from enum import Enum

from auth import get_current_user


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class DeliveryBase(BaseModel):
    description: str
    address: str
    contact_phone: str
    delivery_time: Optional[datetime] = None


class DeliveryCreate(DeliveryBase):
    pass


class Delivery(DeliveryBase):
    id: int
    status: DeliveryStatus = DeliveryStatus.PENDING
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: str  # ID пользователя, создавшего доставку


class DeliveryUpdate(BaseModel):
    id: int
    description: Optional[str] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    delivery_time: Optional[datetime] = None
    status: Optional[DeliveryStatus] = None


class DeliveryStatusUpdate(BaseModel):
    id: int
    status: DeliveryStatus


class DeliveryDelete(BaseModel):
    id: int

router = APIRouter(
    prefix="/deliveries",
    tags=["deliveries"],
)

# Имитация БД
deliveries_db: List[Delivery] = []


@router.post("/create", response_model=Delivery, status_code=status.HTTP_201_CREATED)
async def create_delivery(
    delivery: DeliveryCreate, 
    token: str = Depends(get_current_user)
):
    """Создать новую доставку"""
    delivery_id = len(deliveries_db) + 1
    now = datetime.now()
    
    new_delivery = Delivery(
        id=delivery_id,
        **delivery.dict(),
        created_at=now,
        user_id=token,  # Используем токен как ID пользователя (упрощение)
    )
    
    deliveries_db.append(new_delivery)
    return new_delivery


@router.get("/list", response_model=List[Delivery])
async def list_deliveries(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[DeliveryStatus] = None,
    token: str = Depends(get_current_user)
):
    """Получить список доставок с возможностью фильтрации по статусу"""
    if status:
        return [d for d in deliveries_db if d.status == status][skip:skip + limit]
    return deliveries_db[skip:skip + limit]


@router.get("/get", response_model=Delivery)
async def get_delivery(
    delivery_id: int, 
    token: str = Depends(get_current_user)
):
    """Получить информацию о конкретной доставке"""
    for delivery in deliveries_db:
        if delivery.id == delivery_id:
            return delivery
    raise HTTPException(status_code=404, detail="Delivery not found")


@router.put("/update", response_model=Delivery)
async def update_delivery(
    delivery_update: DeliveryUpdate, 
    token: str = Depends(get_current_user)
):
    delivery_id = delivery_update.id

    for i, delivery in enumerate(deliveries_db):
        if delivery.id == delivery_id:
            update_data = delivery_update.dict(exclude={'id'}, exclude_unset=True)
            
            if not update_data:
                raise HTTPException(
                    status_code=400, 
                    detail="At least one field must be updated"
                )

            updated_delivery = delivery.copy(update=update_data)
            updated_delivery.updated_at = datetime.now()
            
            deliveries_db[i] = updated_delivery
            return updated_delivery
            
    raise HTTPException(status_code=404, detail="Delivery not found")


@router.delete("/delete", response_model=Delivery)
async def delete_delivery(
    delivery: DeliveryDelete, 
    token: str = Depends(get_current_user)
):
    delivery_id = delivery.id
    
    for i, item in enumerate(deliveries_db):
        if item.id == delivery_id:
            return deliveries_db.pop(i)
            
    raise HTTPException(status_code=404, detail="Delivery not found")


@router.patch("/update_status", response_model=Delivery)
async def update_delivery_status(
    status_update: DeliveryStatusUpdate, 
    token: str = Depends(get_current_user)
):
    delivery_id = status_update.id
    new_status = status_update.status
    
    for i, delivery in enumerate(deliveries_db):
        if delivery.id == delivery_id:
            updated_delivery = delivery.copy(
                update={"status": new_status, "updated_at": datetime.now()}
            )
            deliveries_db[i] = updated_delivery
            return updated_delivery
            
    raise HTTPException(status_code=404, detail="Delivery not found")
