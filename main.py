from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    area,
    boulder,
    region,
    user,
    stats,
    search,
    recommendation,
)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "https://bleau-info-stats-frontend-948104408177.europe-west1.run.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(boulder.router)
app.include_router(area.router)
app.include_router(region.router)
app.include_router(user.router)
app.include_router(stats.router)
app.include_router(search.router)
app.include_router(recommendation.router)
