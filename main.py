import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from routers import (
    area,
    boulder,
    crag,
    country,
    stats,
    search,
    recommendation,
)

FRONTEND_URL = os.getenv("FRONTEND_URL")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "https://matchit-frontend-13999527716.europe-west1.run.app",
        FRONTEND_URL,
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(boulder.router)
app.include_router(area.router)
app.include_router(country.router)
app.include_router(stats.router)
app.include_router(search.router)
app.include_router(recommendation.router)
app.include_router(crag.router)
