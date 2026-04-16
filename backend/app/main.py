from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import devices, health, organisations

app = FastAPI(title="IoTDash API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(devices.router)
app.include_router(organisations.router)
