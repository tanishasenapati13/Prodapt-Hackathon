"""
AI Resume Screening — FastAPI Backend

Thin API layer that serves pre-scored candidate data to the dashboard.

Endpoints:
  GET  /candidates          → Ranked list of all scored candidates
  GET  /candidates/{id}     → Single candidate result
  POST /match-score         → Score result for a resume/JD pair
  POST /gap-analysis        → Gap analysis (same shape as match-score)
  POST /parse-resume        → Structured resume data

Run:
  uvicorn api.main:app --reload --port 8001
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import matching, resume, candidates

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(asctime)s %(name)s %(message)s")
logger = logging.getLogger("api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    from api.data.store import get_all_results
    results = get_all_results()
    logger.info("Resume Screening API started — serving %d pre-loaded results from results.json", len(results))
    yield
    logger.info("Resume Screening API shutting down")

app = FastAPI(
    title="AI Resume Screening API",
    description="Backend API for the Prodapt Hackathon Resume Screening Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matching.router)
app.include_router(resume.router)
app.include_router(candidates.router)

@app.get("/", tags=["Health"])
async def health():
    return {"status": "ok", "service": "AI Resume Screening API"}
