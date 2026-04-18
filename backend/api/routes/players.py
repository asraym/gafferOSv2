from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from db.database import get_db
from db.models import Player, PlayerSeasonStats, PlayerMatchSnapshot, Club, Team, Season
from core.csv_importer import CSVImporter

router = APIRouter()
csv_importer = CSVImporter()

VALID_BROAD    = ["GK", "DEF", "MID", "FWD"]
VALID_SPECIFIC = ["GK", "CB", "RB", "LB", "RWB", "LWB",
                  "CDM", "CM", "CAM", "RM", "LM",
                  "RW", "LW", "ST", "CF", "SS"]


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

    if request.broad_position not in VALID_BROAD:
        raise HTTPException(status_code=400, detail=f"Invalid broad position. Must be one of {VALID_BROAD}")

    if request.specific_position not in VALID_SPECIFIC:
        raise HTTPException(status_code=400, detail=f"Invalid specific position. Must be one of {VALID_SPECIFIC}")

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
        "player_id":      player_id,
        "player_name":    player.name,
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