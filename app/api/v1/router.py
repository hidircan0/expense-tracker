from fastapi import APIRouter

from app.api.v1.endpoints import analytics, auth, categories, expenses

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
