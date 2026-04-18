from fastapi import APIRouter
from api.routes import players, matches, opposition

router = APIRouter()
router.include_router(opposition.router, tags=["Opposition"])
router.include_router(players.router, tags=["Players"])
router.include_router(matches.router, tags=["Matches"])