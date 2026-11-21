from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Product
from app.schemas import ProductCreate, ProductOut

from pydantic import BaseModel

app = FastAPI()

@app.get('/health')
def get_health():
    return {'status': 'ok'}

class DbCheckOut(BaseModel):
    result: int

@app.get('/dbcheck', response_model=DbCheckOut)
async def get_dbcheck(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text('SELECT 1'))
    return DbCheckOut(result=result.scalar_one())

@app.get('/products', response_model=list[ProductOut])
async def get_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product))        
    return result.scalars().all()

@app.get('/products/{id}', response_model=ProductOut)
async def get_product_by_id(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404,detail=f'No product exists with id {id}')
    else:
        return product

@app.post('/products', response_model=ProductOut)
# @TODO restrict to admin role
async def post_products(product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    new_product = Product(**product_in.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product
