from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    area,
    boulder,
    country,
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
        "",
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
