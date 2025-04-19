# This file makes the directory a Python package
from fastapi import APIRouter

router = APIRouter()

from .jobs import router as jobs_router
from .generate import router as generate_router

router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
router.include_router(generate_router, prefix="/generate", tags=["generate"])