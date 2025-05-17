from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class InventoryItemBase(BaseModel):
    name: str
    category: str
    quantity: int
    price: float
    image_url: str = ""
    description: Optional[str] = None

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(InventoryItemBase):
    pass

class InventoryItemResponse(InventoryItemBase):
    id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool = True
    is_admin: bool = False

    class Config:
        from_attributes = True

# Order schemas
class OrderItemBase(BaseModel):
    inventory_id: int
    quantity: int

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    price_at_time: float
    inventory_item: Optional[InventoryItemResponse] = None

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    status: str = "pending"

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    supplier: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None
    is_purchase_order: Optional[bool] = False

class Order(OrderBase):
    id: int
    user_id: int
    total_amount: float
    created_at: datetime
    updated_at: datetime
    supplier: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None
    is_purchase_order: Optional[bool] = False
    items: List[OrderItem] = []

    class Config:
        from_attributes = True

class OrderUpdate(BaseModel):
    status: str

    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
