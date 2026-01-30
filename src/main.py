from fastapi import FastAPI
from routes.cv_routes import router as cv_router

app = FastAPI(title="Scout Talent AI")

# TODO: Add startup/shutdown handlers
# TODO: Add routers
app.include_router(cv_router)