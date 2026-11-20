from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

app = FastAPI()

@app.get('/health')
def get_health():
    return {'status': 'ok'}

@app.get('/dbcheck')
async def get_dbcheck(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text('SELECT 1'))
    return {'result': result.scalar()}