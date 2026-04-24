from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin_device_types, admin_devices, admin_orgs, admin_users, alerts, auth, devices, health, metrics, organisations

app = FastAPI(title="IoTDash API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(organisations.router)
app.include_router(alerts.router)
app.include_router(metrics.router)
app.include_router(admin_orgs.router)
app.include_router(admin_users.router)
app.include_router(admin_devices.router)
app.include_router(admin_device_types.router)
