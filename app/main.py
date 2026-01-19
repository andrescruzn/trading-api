from fastapi import FastAPI

from app.modules.users.rest.routes import router as meta_router

app = FastAPI(title="FastAPI Sync + MySQL")
app.include_router(meta_router)