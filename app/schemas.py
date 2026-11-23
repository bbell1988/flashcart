from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    price_cents: int
    stock_qty: int
    is_active: bool = True


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price_cents: int
    stock_qty: int
    is_active: bool

class UserCreate(BaseModel):

    name: str
    email: str
    password: str
    role: str = 'customer'
    is_active: bool = True

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    is_active: bool

class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class OrderItemCreate(BaseModel):

    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: list[OrderItemCreate]

class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    price_at_purchase: int

class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    status: str
    items: list[OrderItemOut]