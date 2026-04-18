from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from db.database import get_db
from db.models import Match, PlayerMatchSnapshot, PlayerSeasonStats

router = APIRouter()


# --- Match Registration ---

class MatchRegisterRequest(BaseModel):
    season_id: int
    team_id: int
    opponent_name: str
    match_date: str  # YYYY-MM-DD
    venue: Optional[str] = "home"  # home / away / neutral


@router.post("/matches/register")
def register_match(req: MatchRegisterRequest, db: Session = Depends(get_db)):
    match = Match(
        season_id     = req.season_id,
        team_id       = req.team_id,
        opponent_name = req.opponent_name,
        match_date    = req.match_date,
        venue         = req.venue,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return {
        "match_id":      match.id,
        "opponent_name": match.opponent_name,
        "match_date":    str(match.match_date),
    }


# --- Player Match Snapshot ---

class SnapshotRequest(BaseModel):
    match_id: int
    player_id: int
    minutes_played: int = 0
    was_starter: bool = False
    goals: int = 0
    assists: int = 0
    shots: int = 0
    key_passes: int = 0
    passes_completed: int = 0
    passes_attempted: int = 0
    tackles: int = 0
    interceptions: int = 0
    defensive_errors: int = 0
    saves: int = 0


@router.post("/matches/snapshot")
def write_snapshot(req: SnapshotRequest, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == req.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found.")

    existing = db.query(PlayerMatchSnapshot).filter_by(
        player_id=req.player_id, match_id=req.match_id
    ).first()

    if existing:
        for field, value in req.dict().items():
            setattr(existing, field, value)
    else:
        existing = PlayerMatchSnapshot(
            season_id = match.season_id,
            **req.dict()
        )
        db.add(existing)

    db.flush()

    all_snapshots = db.query(PlayerMatchSnapshot).filter(
        PlayerMatchSnapshot.player_id == req.player_id
    ).all()

    totals = {
        "matches_played":   len(all_snapshots),
        "goals":            sum(s.goals for s in all_snapshots),
        "assists":          sum(s.assists for s in all_snapshots),
        "shots":            sum(s.shots for s in all_snapshots),
        "key_passes":       sum(s.key_passes for s in all_snapshots),
        "passes_completed": sum(s.passes_completed for s in all_snapshots),
        "passes_attempted": sum(s.passes_attempted for s in all_snapshots),
        "tackles":          sum(s.tackles for s in all_snapshots),
        "interceptions":    sum(s.interceptions for s in all_snapshots),
        "defensive_errors": sum(s.defensive_errors for s in all_snapshots),
        "saves":            sum(s.saves for s in all_snapshots),
        "minutes_played":   sum(s.minutes_played for s in all_snapshots),
    }

    season_stats = db.query(PlayerSeasonStats).filter_by(
        player_id=req.player_id, season_id=match.season_id
    ).first()

    if season_stats:
        for field, value in totals.items():
            setattr(season_stats, field, value)
    else:
        season_stats = PlayerSeasonStats(
            player_id = req.player_id,
            season_id = match.season_id,
            **totals
        )
        db.add(season_stats)

    db.commit()
    return {
        "status":        "ok",
        "player_id":     req.player_id,
        "match_id":      req.match_id,
        "season_totals": totals,
    }