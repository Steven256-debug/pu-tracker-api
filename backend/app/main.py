"""
PU Academic Performance Tracker — API backend.

This service exists for exactly two reasons that cannot be done in the
browser: running the trained LightGBM model, and generating PDF reports
with reportlab. Everything else (UI, state, charts, search/filter) lives
in the React frontend.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, predict, reports, meta

app = FastAPI(
    title="PU Academic Performance Tracker API",
    description="Prediction and reporting backend for the Pentecost University "
                "Academic Risk Intelligence System.",
    version="1.0.0",
)

# CORS — the frontend on Vercel calls this API from a different origin.
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(reports.router)
app.include_router(meta.router)


@app.get("/")
def root():
    return {
        "service": "PU Academic Performance Tracker API",
        "status": "running",
        "docs": "/docs",
    }
