from contextlib import asynccontextmanager
from fastapi import FastAPI
from data.data import create_db_and_tables
from routers import auth,summary,expenses,category
@asynccontextmanager
async def lifespan(app:FastAPI):
    create_db_and_tables
    yield
app=FastAPI(title="Expense tracker API",lifespan=lifespan)
app.include_router(auth.router)
app.include_router(category.router)
app.include_router(expenses.router)
app.include_router(summary.router)