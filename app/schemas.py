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
