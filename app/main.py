import logging
import os
from fastapi import FastAPI
from app.api.routes import router
from app.db.database import create_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s – %(message)s",
)

app = FastAPI(
    title="VoltEdge – Charging Session API",
    description="MVP til styring af EV-ladesessioner. Domain Driven Design med FastAPI og PostgreSQL.",
    version="1.0.0",
)

app.include_router(router)


@app.on_event("startup")
def startup():
    create_tables()


@app.get("/health")
def health():
    return {"status": "ok", "service": "voltedge-session"}
