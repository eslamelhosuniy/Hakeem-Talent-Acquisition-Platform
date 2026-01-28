from fastapi import APIRouter, Depends
from helpers.config import get_settings, Settings

main_router = APIRouter()
base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)

@main_router.get("/")
async def root(app_settings: Settings = Depends(get_settings)):
    return {
        f"Welcome to the {app_settings.APP_NAME} Platform API {app_settings.APP_VERSION}"
    }
    
@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)):
    return {
        "app_name": app_settings.APP_NAME,
        "app_version": app_settings.APP_VERSION,
    }

