from fastapi import APIRouter

from app.api.v1 import categories, health, products
from app.api.v1.admin import auth as admin_auth
from app.api.v1.admin import categories as admin_categories
from app.api.v1.admin import products as admin_products
from app.api.v1.admin import users as admin_users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(categories.router)
api_router.include_router(products.router)

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(admin_auth.router)
admin_router.include_router(admin_users.router)
admin_router.include_router(admin_categories.router)
admin_router.include_router(admin_products.router)
api_router.include_router(admin_router)
