from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from db.database import get_db
from db.models import OppositionProfile, Match, Player, PlayerSeasonStats, Club, Team, Season, PlayerMatchSnapshot
from core.opposition_parser import OppositionParser
from core.csv_importer import CSVImporter

router = APIRouter()
parser = OppositionParser()
csv_importer = CSVImporter()


# --- Opposition Parser ---

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
    match = db.query(Match).filter(Match.id == request.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found.")

    parsed = parser.parse(request.notes)

    existing = db.query(OppositionProfile).filter(
        OppositionProfile.match_id == request.match_id
    ).first()

    if existing:
        existing.likely_formation   = parsed["likely_formation"]
        existing.press_style        = parsed["press_style"]
        existing.defensive_line     = parsed["defensive_line"]
        existing.playing_style      = parsed["playing_style"]
        existing.set_piece_threat   = parsed["set_piece_threat"]
        existing.attributes         = parsed["attributes"]
        existing.raw_scouting_notes = parsed["raw_scouting_notes"]
        db.commit()
        db.refresh(existing)
        profile = existing
    else:
        profile = OppositionProfile(
            match_id            = request.match_id,
            opponent_name       = request.opponent_name,
            likely_formation    = parsed["likely_formation"],
            press_style         = parsed["press_style"],
            defensive_line      = parsed["defensive_line"],
            playing_style       = parsed["playing_style"],
            set_piece_threat    = parsed["set_piece_threat"],
            attributes          = parsed["attributes"],
            raw_scouting_notes  = parsed["raw_scouting_notes"],
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return ScoutingNotesResponse(
        match_id            = profile.match_id,
        opponent_name       = profile.opponent_name,
        likely_formation    = profile.likely_formation,
        press_style         = profile.press_style,
        defensive_line      = profile.defensive_line,
        playing_style       = profile.playing_style,
        set_piece_threat    = profile.set_piece_threat,
        attributes          = profile.attributes or {},
        raw_scouting_notes  = profile.raw_scouting_notes,
    )


# --- Player Registration ---

class PlayerRegistrationRequest(BaseModel):
    club_id: int
    team_id: int
    name: str
    broad_position: str
    specific_position: str
    secondary_position: Optional[str] = None
    jersey_number: Optional[int] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None


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
    club = db.query(Club).filter(Club.id == request.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")

    team = db.query(Team).filter(Team.id == request.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")

    valid_broad = ["GK", "DEF", "MID", "FWD"]
    valid_specific = ["GK", "CB", "RB", "LB", "RWB", "LWB",
                      "CDM", "CM", "CAM", "RM", "LM",
                      "RW", "LW", "ST", "CF", "SS"]

    if request.broad_position not in valid_broad:
        raise HTTPException(status_code=400, detail=f"Invalid broad position. Must be one of {valid_broad}")

    if request.specific_position not in valid_specific:
        raise HTTPException(status_code=400, detail=f"Invalid specific position. Must be one of {valid_specific}")

    dob = None
    if request.date_of_birth:
        try:
            dob = date.fromisoformat(request.date_of_birth)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    player = Player(
        club_id             = request.club_id,
        name                = request.name,
        broad_position      = request.broad_position,
        specific_position   = request.specific_position,
        secondary_position  = request.secondary_position,
        jersey_number       = request.jersey_number,
        nationality         = request.nationality,
        date_of_birth       = dob,
        is_active           = True,
    )
    db.add(player)
    db.flush()

    active_season = db.query(Season).filter(
        Season.club_id   == request.club_id,
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


# --- CSV Import ---

class CSVImportResponse(BaseModel):
    total_rows: int
    imported: int
    skipped: int
    errors: list
    players: list


@router.post("/players/import-csv", response_model=CSVImportResponse)
async def import_players_csv(
    club_id: int,
    team_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv file.")

    file_bytes = await file.read()
    result = csv_importer.parse(file_bytes)

    if not result["valid"] and result["errors"]:
        raise HTTPException(status_code=400, detail=result["errors"])

    active_season = db.query(Season).filter(
        Season.club_id   == club_id,
        Season.is_active == True
    ).first()

    imported = []

    for row in result["valid"]:
        dob = None
        if row["date_of_birth"]:
            try:
                dob = date.fromisoformat(row["date_of_birth"])
            except ValueError:
                pass

        player = Player(
            club_id             = club_id,
            name                = row["name"],
            broad_position      = row["broad_position"],
            specific_position   = row["specific_position"],
            secondary_position  = row["secondary_position"],
            jersey_number       = row["jersey_number"],
            nationality         = row["nationality"],
            date_of_birth       = dob,
            is_active           = True,
        )
        db.add(player)
        db.flush()

        if active_season:
            stats_row = PlayerSeasonStats(
                player_id = player.id,
                season_id = active_season.id,
                team_id   = team_id,
            )
            db.add(stats_row)

        imported.append({
            "player_id":         player.id,
            "name":              player.name,
            "specific_position": player.specific_position,
            "jersey_number":     player.jersey_number,
        })

    db.commit()

    return CSVImportResponse(
        total_rows = len(result["valid"]) + len(result["errors"]),
        imported   = len(imported),
        skipped    = len(result["errors"]),
        errors     = result["errors"],
        players    = imported,
    )


# --- Match Registration ---

class MatchRegisterRequest(BaseModel):
    season_id: int
    team_id: int
    opponent_name: str
    match_date: str  # YYYY-MM-DD
    venue: Optional[str] = "home"


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


# --- Player List ---

@router.get("/players")
def list_players(team_id: int, db: Session = Depends(get_db)):
    players = (
        db.query(Player)
        .join(PlayerSeasonStats, PlayerSeasonStats.player_id == Player.id)
        .filter(PlayerSeasonStats.team_id == team_id)
        .order_by(Player.jersey_number)
        .all()
    )
    return [
        {
            "id":                p.id,
            "name":              p.name,
            "broad_position":    p.broad_position,
            "specific_position": p.specific_position,
            "jersey_number":     p.jersey_number,
        }
        for p in players
    ]


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
    # Get match first so we have season_id
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

# --- Player Form Curve ---

@router.get("/players/{player_id}/form")
def player_form(player_id: int, n: int = 5, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found.")

    snapshots = (
        db.query(PlayerMatchSnapshot)
        .filter(PlayerMatchSnapshot.player_id == player_id)
        .order_by(PlayerMatchSnapshot.match_id.desc())
        .limit(n)
        .all()
    )

    return {
        "player_id":     player_id,
        "player_name":   player.name,
        "last_n_matches": n,
        "snapshots": [
            {
                "match_id":          s.match_id,
                "minutes_played":    s.minutes_played,
                "was_starter":       s.was_starter,
                "goals":             s.goals,
                "assists":           s.assists,
                "shots":             s.shots,
                "key_passes":        s.key_passes,
                "passes_completed":  s.passes_completed,
                "passes_attempted":  s.passes_attempted,
                "tackles":           s.tackles,
                "interceptions":     s.interceptions,
                "defensive_errors":  s.defensive_errors,
                "saves":             s.saves,
            }
            for s in snapshots
        ],
    }