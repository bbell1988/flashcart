from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import User, Product, Order, OrderItem
from app.schemas import (
    UserCreate,
    UserOut,
    ProductCreate,
    ProductOut,
    OrderCreate,
    OrderOut,
    LoginRequest,
    Token
)

from pydantic import BaseModel

from app.security import (
    get_current_user,
    hash_password,
    verify_password,
    create_access_token,
    require_role
)

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
async def post_products(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin'))):
    new_product = Product(**product_in.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

@app.post('/register', response_model=UserOut)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):

    hashed_password = hash_password(user_in.password)
    new_user = User(name=user_in.name, email=user_in.email, password_hash=hashed_password)
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user    
    except IntegrityError as e:
        await db.rollback()
        if 'ix_users_email' in str(e.orig):
            raise HTTPException(status_code=409, detail="email already registered")
        raise

@app.post('/auth/login', response_model=Token)
async def login_user(login_in: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email==login_in.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(status_code=401,detail='Invalid email or password')
    else:
        access_token = create_access_token({'sub': str(user.id)})
        return Token(access_token=access_token)

@app.get('/me', response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post('/orders', response_model=OrderOut)
async def place_order(
    order_in: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    products: dict[int, Product] = {}

    for item in order_in.items:
        result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = result.scalar_one_or_none()

        if product is None:
            raise HTTPException(status_code=404, detail=f'No product exists with id {item.product_id}')
        if product.stock_qty < item.quantity:
            raise HTTPException(status_code=400, detail=f'Insufficient stock for product {item.product_id}')

        products[item.product_id] = product

    new_order = Order(user_id=current_user.id)
    db.add(new_order)
    await db.flush()

    for item in order_in.items:
        product = products[item.product_id]
        product.stock_qty -= item.quantity

        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=product.price_cents,
        )
        db.add(order_item)

    await db.commit()
    await db.refresh(new_order, attribute_names=["items"])
    return new_order

