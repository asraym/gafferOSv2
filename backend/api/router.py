from fastapi import APIRouter
from api import auth
from api.routes import players, matches, opposition

router = APIRouter()
router.include_router(auth.router, tags=["Auth"])
router.include_router(opposition.router, tags=["Opposition"])
router.include_router(players.router, tags=["Players"])
router.include_router(matches.router, tags=["Matches"])