from fastapi import FastAPI
from routers import auth,summary,expenses,category

app=FastAPI(title="Expense tracker API")
app.include_router(auth.router)
app.include_router(category.router)
app.include_router(expenses.router)
app.include_router(summary.router)