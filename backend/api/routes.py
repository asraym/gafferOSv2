from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from db.models import OppositionProfile, Match
from core.opposition_parser import OppositionParser

router = APIRouter()
parser = OppositionParser()


class ScoutingNotesRequest(BaseModel):
    match_id: int
    opponent_name: str
    notes: str


class ScoutingNotesResponse(BaseModel):
    match_id: int
    opponent_name: str
    likely_formation: str | None
    press_style: str | None
    defensive_line: str | None
    playing_style: str | None
    set_piece_threat: str | None
    attributes: dict
    raw_scouting_notes: str


@router.post("/opposition/parse", response_model=ScoutingNotesResponse)
def parse_opposition(request: ScoutingNotesRequest, db: Session = Depends(get_db)):

    # Check match exists
    match = db.query(Match).filter(Match.id == request.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found.")

    # Parse the notes
    parsed = parser.parse(request.notes)

    # Check if profile already exists for this match
    existing = db.query(OppositionProfile).filter(
        OppositionProfile.match_id == request.match_id
    ).first()

    if existing:
        # Update existing profile
        existing.likely_formation  = parsed["likely_formation"]
        existing.press_style       = parsed["press_style"]
        existing.defensive_line    = parsed["defensive_line"]
        existing.playing_style     = parsed["playing_style"]
        existing.set_piece_threat  = parsed["set_piece_threat"]
        existing.attributes        = parsed["attributes"]
        existing.raw_scouting_notes = parsed["raw_scouting_notes"]
        db.commit()
        db.refresh(existing)
        profile = existing
    else:
        # Create new profile
        profile = OppositionProfile(
            match_id           = request.match_id,
            opponent_name      = request.opponent_name,
            likely_formation   = parsed["likely_formation"],
            press_style        = parsed["press_style"],
            defensive_line     = parsed["defensive_line"],
            playing_style      = parsed["playing_style"],
            set_piece_threat   = parsed["set_piece_threat"],
            attributes         = parsed["attributes"],
            raw_scouting_notes = parsed["raw_scouting_notes"],
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return ScoutingNotesResponse(
        match_id           = profile.match_id,
        opponent_name      = profile.opponent_name,
        likely_formation   = profile.likely_formation,
        press_style        = profile.press_style,
        defensive_line     = profile.defensive_line,
        playing_style      = profile.playing_style,
        set_piece_threat   = profile.set_piece_threat,
        attributes         = profile.attributes or {},
        raw_scouting_notes = profile.raw_scouting_notes,
    )