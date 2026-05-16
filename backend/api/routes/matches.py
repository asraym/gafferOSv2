from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from db.database import get_db
from db.models import Match, PlayerMatchSnapshot, PlayerSeasonStats
from datetime import date as date_type
from core.tactical_engine import TacticalEngine

router = APIRouter()
_engine = TacticalEngine()

class AnalyseRequest(BaseModel):
    match_id: int
    team_id: int

@router.post("/analyse")
def analyse_match(req: AnalyseRequest, db: Session = Depends(get_db)):
    try:
        result = _engine.analyse(db, req.match_id, req.team_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")



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

@router.get("/matches/upcoming")
def get_upcoming_matches(team_id: int, db: Session = Depends(get_db)):
    match = (
        db.query(Match)
        .filter(
            Match.team_id == team_id,
            Match.match_date >= date_type.today(),
            Match.result == None
        )
        .order_by(Match.match_date.asc())
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="No upcoming match found. ")
    return {
        "match_id": match.id,
        "opponent_name": match.opponent_name,
        "match_date": str(match.match_date),
        "venue": match.venue,
    }

class MatchFeedbackRequest(BaseModel):
    match_id:              int
    actual_result:         str           # W / D / L
    formation_used:        str
    goals_scored:          int
    goals_conceded:        int
    coach_notes:           Optional[str] = None
    # Tactical context — stored for model training (#2 feedback loop)
    coach_followed_rec:    Optional[bool] = None   # did coach play recommended formation
    recommended_formation: Optional[str]  = None   # what engine recommended
    recommended_line:      Optional[str]  = None
    recommended_press:     Optional[str]  = None
    recommended_focus:     Optional[str]  = None
    predicted_win_prob:    Optional[float] = None
    squad_style:           Optional[str]  = None   # style label e.g. "direct"
    coherence_score:       Optional[float] = None
    opponent_style:        Optional[str]  = None


@router.post("/matches/feedback")
def record_match_feedback(req: MatchFeedbackRequest, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == req.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found.")

    allowed_results = {"W", "D", "L"}
    if req.actual_result not in allowed_results:
        raise HTTPException(
            status_code=400,
            detail=f"actual_result must be one of {allowed_results}"
        )

    match.result         = req.actual_result
    match.formation_used = req.formation_used
    match.goals_scored   = req.goals_scored
    match.goals_conceded = req.goals_conceded
    if req.coach_notes:
        match.notes = req.coach_notes

    # Tactical context fields — store if columns exist
    # Add these to Match model and run migration if not present
    for field in [
        "coach_followed_rec", "recommended_formation", "recommended_line",
        "recommended_press", "recommended_focus", "predicted_win_prob",
        "squad_style", "coherence_score", "opponent_style",
    ]:
        val = getattr(req, field, None)
        if val is not None and hasattr(match, field):
            setattr(match, field, val)

    db.commit()

    return {
        "status":           "recorded",
        "match_id":         req.match_id,
        "actual_result":    req.actual_result,
        "formation_used":   req.formation_used,
        "coherence_score":  req.coherence_score,
        "followed_rec":     req.coach_followed_rec,
    }