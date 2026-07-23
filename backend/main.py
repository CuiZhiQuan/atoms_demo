from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from backend.config import PROJECTS_DIR
from backend.api.routes import router
from backend.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    yield


app = FastAPI(title="Atoms MVP", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount workspace for preview
os.makedirs(PROJECTS_DIR, exist_ok=True)
app.mount("/workspace", StaticFiles(directory=PROJECTS_DIR, html=True), name="workspace")

# Include API routes
app.include_router(router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}