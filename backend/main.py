"""FastAPI application entry point."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models
from .routers import alerts, devices, statistics, traffic

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Intelligent Network Traffic Analyzer", version="1.0.0", description="Backend API for monitored traffic, devices, statistics, and alerts.")
origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080,http://localhost:8000,http://127.0.0.1:8000").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Content-Type"])
app.include_router(traffic.router)
app.include_router(statistics.router)
app.include_router(alerts.router)
app.include_router(devices.router)

@app.get("/api/health", tags=["health"])
def health(): return {"status": "ok"}
