from contextlib import asynccontextmanager
from fastapi import FastAPI
from data.data import create_db_and_tables
from routers import auth
@asynccontextmanager
async def lifespan(app:FastAPI):
    create_db_and_tables
    yield
app=FastAPI(title="Expense tracker API",lifespan=lifespan)
app.include_router(auth.router)