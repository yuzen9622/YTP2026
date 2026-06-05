"""API v1 root router."""
from fastapi import APIRouter

from app.interfaces.api.v1.admin.router import router as admin_router
from app.interfaces.api.v1.auth.router import router as auth_router
from app.interfaces.api.v1.chat.router import router as chat_router

from app.interfaces.api.v1.rag.router import router as rag_router

from app.interfaces.api.v1.customer_service.router import router as customer_service_router

from app.interfaces.api.v1.resumes.router import router as resumes_router
from app.interfaces.api.v1.users.router import router as users_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(chat_router)

api_v1_router.include_router(rag_router)

api_v1_router.include_router(customer_service_router)

api_v1_router.include_router(resumes_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(admin_router)
