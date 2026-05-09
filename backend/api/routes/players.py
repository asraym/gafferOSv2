from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from db.database import get_db
from db.models import Player, PlayerSeasonStats, PlayerMatchSnapshot, Club, Team, Season, PlayerPositionalAnswers, PlayerPhysicalAttributes, PlayerAttributeProfile, Season
from core.csv_importer import CSVImporter
from core.player_traits import validate_traits, get_traits_for_position, get_tactical_profile
from core.attribute_calculator import calculate_attributes, calculate_role_rating, calculate_overall_rating

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
    try:
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
        )
        db.add(player)
        db.flush()

        active_season = db.query(Season).filter(
            Season.club_id   == request.club_id,
            Season.is_active == True
        ).first()

        season_stats_created = False
        season_label = active_season.label

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
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


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

class TraitSubmission(BaseModel):
    season_id:         int
    specific_position: str
    traits:            list[str]


@router.post("/{player_id}/traits")
def save_player_traits(player_id: int, payload: TraitSubmission, db: Session = Depends(get_db)):
    # Check player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found.")

    # Validate traits
    validation = validate_traits(payload.specific_position, payload.traits)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail={
            "message":        "Invalid trait selection.",
            "errors":         validation["errors"],
            "invalid_traits": validation["invalid_traits"],
        })

    # Upsert — overwrite if already exists for this player/season/position
    existing = (
        db.query(PlayerPositionalAnswers)
        .filter(
            PlayerPositionalAnswers.player_id == player_id,
            PlayerPositionalAnswers.season_id == payload.season_id,
            PlayerPositionalAnswers.position  == payload.specific_position,
        )
        .first()
    )

    if existing:
        existing.answers = {"traits": payload.traits}
    else:
        db.add(PlayerPositionalAnswers(
            player_id = player_id,
            season_id = payload.season_id,
            position  = payload.specific_position,
            answers   = {"traits": payload.traits},
        ))

    db.commit()

    # Return tactical profile derived from these traits
    profile = get_tactical_profile(payload.traits)
    return {
        "player_id":        player_id,
        "position":         payload.specific_position,
        "traits_saved":     payload.traits,
        "tactical_profile": profile,
    }


@router.get("/{player_id}/traits")
def get_player_traits(player_id: int, season_id: int, specific_position: str, db: Session = Depends(get_db)):
    # Check player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found.")

    # Get valid traits for this position
    valid_traits = get_traits_for_position(specific_position)

    # Get saved traits if any
    saved = (
        db.query(PlayerPositionalAnswers)
        .filter(
            PlayerPositionalAnswers.player_id == player_id,
            PlayerPositionalAnswers.season_id == season_id,
            PlayerPositionalAnswers.position  == specific_position,
        )
        .first()
    )

    selected_traits  = saved.answers.get("traits", []) if saved else []
    tactical_profile = get_tactical_profile(selected_traits) if selected_traits else {}

    return {
        "player_id":         player_id,
        "position":          specific_position,
        "available_traits":  valid_traits,
        "selected_traits":   selected_traits,
        "tactical_profile":  tactical_profile,
    }

class PhysicalAssessment(BaseModel):
    height_cm:        Optional[float] = None
    weight_kg:        Optional[float] = None
    beep_test_level:  Optional[float] = None
    sprint_time_20m:  Optional[float] = None
    vertical_jump_cm: Optional[float] = None
    date_assessed:    Optional[str]   = None
@router.post("/{player_id}/physical")
def submit_physical_assessment(
    player_id: int,
    payload: PhysicalAssessment,
    db: Session = Depends(get_db)
):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found.")

    active_season = db.query(Season).filter(Season.is_active == True).first()
    if not active_season:
        raise HTTPException(status_code=404, detail="No active season found.")

    # Upsert physical attributes
    physical = (
        db.query(PlayerPhysicalAttributes)
        .filter(
            PlayerPhysicalAttributes.player_id == player_id,
            PlayerPhysicalAttributes.season_id == active_season.id,
        )
        .first()
    )

    physical_dict = payload.dict()

    if physical:
        for key, val in physical_dict.items():
            if val is not None:
                setattr(physical, key, val)
    else:
        physical = PlayerPhysicalAttributes(
            player_id = player_id,
            season_id = active_season.id,
            **{k: v for k, v in physical_dict.items() if v is not None}
        )
        db.add(physical)

    db.flush()

    # Build player dict for attribute calculator
    season_stats = (
        db.query(PlayerSeasonStats)
        .filter(
            PlayerSeasonStats.player_id == player_id,
            PlayerSeasonStats.season_id == active_season.id,
        )
        .first()
    )

    player_data = {
        "season_goals":            season_stats.goals or 0 if season_stats else 0,
        "season_assists":          season_stats.assists or 0 if season_stats else 0,
        "season_shots":            season_stats.shots or 0 if season_stats else 0,
        "season_key_passes":       season_stats.key_passes or 0 if season_stats else 0,
        "season_passes_completed": season_stats.passes_completed or 0 if season_stats else 0,
        "season_passes_attempted": season_stats.passes_attempted or 0 if season_stats else 0,
        "season_tackles":          season_stats.tackles or 0 if season_stats else 0,
        "season_interceptions":    season_stats.interceptions or 0 if season_stats else 0,
        "season_defensive_errors": season_stats.defensive_errors or 0 if season_stats else 0,
        "season_saves":            season_stats.saves or 0 if season_stats else 0,
        "season_matches_played":   season_stats.matches_played or 0 if season_stats else 0,
    }

    physical_data = {
        "height_cm":        physical.height_cm,
        "weight_kg":        physical.weight_kg,
        "beep_test_level":  physical.beep_test_level,
        "sprint_time_20m":  physical.sprint_time_20m,
        "vertical_jump_cm": physical.vertical_jump_cm,
    }

    # Calculate attributes
    attributes  = calculate_attributes(player_data, physical_data)
    role_rating = calculate_role_rating(attributes, player.specific_position)
    overall     = calculate_overall_rating(attributes, role_rating)

    # Upsert attribute profile
    profile = (
        db.query(PlayerAttributeProfile)
        .filter(
            PlayerAttributeProfile.player_id == player_id,
            PlayerAttributeProfile.season_id == active_season.id,
        )
        .first()
    )

    if profile:
        for attr, val in attributes.items():
            if val is not None:
                setattr(profile, attr, val)
        profile.role_rating    = role_rating
        profile.overall_rating = overall
    else:
        db.add(PlayerAttributeProfile(
            player_id      = player_id,
            season_id      = active_season.id,
            role_rating    = role_rating,
            overall_rating = overall,
            **{k: v for k, v in attributes.items() if v is not None}
        ))

    db.commit()

    return {
        "player_id":      player_id,
        "player_name":    player.name,
        "position":       player.specific_position,
        "attributes":     attributes,
        "role_rating":    role_rating,
        "overall_rating": overall,
    }