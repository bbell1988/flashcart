from pydantic import BaseModel, ConfigDict

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
