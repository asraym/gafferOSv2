from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from db.database import get_db
from db.models import OppositionProfile, Match, Player, PlayerSeasonStats, Club, Team, Season
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

class PlayerRegistrationRequest(BaseModel):
    club_id: int
    team_id: int
    name: str
    broad_position: str        # GK, DEF, MID, FWD
    specific_position: str     # CB, CM, ST etc
    secondary_position: Optional[str] = None
    jersey_number: Optional[int] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None  # format: YYYY-MM-DD


class PlayerRegistrationResponse(BaseModel):
    player_id: int
    name: str
    broad_position: str
    specific_position: str
    jersey_number: Optional[int]
    season_stats_created: bool
    season_label: Optional[str]
    message: str


@router.post("/players/register", response_model=PlayerRegistrationResponse)
def register_player(request: PlayerRegistrationRequest, db: Session = Depends(get_db)):

    # Validate club exists
    club = db.query(Club).filter(Club.id == request.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")

    # Validate team exists
    team = db.query(Team).filter(Team.id == request.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")

    # Validate position values
    valid_broad = ["GK", "DEF", "MID", "FWD"]
    valid_specific = ["GK", "CB", "RB", "LB", "RWB", "LWB",
                      "CDM", "CM", "CAM", "RM", "LM",
                      "RW", "LW", "ST", "CF", "SS"]

    if request.broad_position not in valid_broad:
        raise HTTPException(status_code=400, detail=f"Invalid broad position. Must be one of {valid_broad}")

    if request.specific_position not in valid_specific:
        raise HTTPException(status_code=400, detail=f"Invalid specific position. Must be one of {valid_specific}")

    # Parse date of birth if provided
    from datetime import date
    dob = None
    if request.date_of_birth:
        try:
            dob = date.fromisoformat(request.date_of_birth)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    # Create the player
    player = Player(
        club_id            = request.club_id,
        name               = request.name,
        broad_position     = request.broad_position,
        specific_position  = request.specific_position,
        secondary_position = request.secondary_position,
        jersey_number      = request.jersey_number,
        nationality        = request.nationality,
        date_of_birth      = dob,
        is_active          = True,
    )
    db.add(player)
    db.flush()  # gets us the player.id without committing yet

    # Find active season for this club
    active_season = db.query(Season).filter(
        Season.club_id  == request.club_id,
        Season.is_active == True
    ).first()

    season_stats_created = False
    season_label = None

    if active_season:
        stats_row = PlayerSeasonStats(
            player_id = player.id,
            season_id = active_season.id,
            team_id   = request.team_id,
        )
        db.add(stats_row)
        season_stats_created = True
        season_label = active_season.label

    db.commit()
    db.refresh(player)

    return PlayerRegistrationResponse(
        player_id            = player.id,
        name                 = player.name,
        broad_position       = player.broad_position,
        specific_position    = player.specific_position,
        jersey_number        = player.jersey_number,
        season_stats_created = season_stats_created,
        season_label         = season_label,
        message              = f"{player.name} registered successfully. Player ID: {player.id}"
    )