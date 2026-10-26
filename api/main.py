"""FastAPI app: CORS, routers, startup data load (Day 2 hello-world, grows from Day 3)."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import health

app = FastAPI(title="SafeHaven API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
