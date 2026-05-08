from sqlalchemy import Column, Integer, String, Float, Boolean, Text, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
from datetime import datetime


class Club(Base):
    __tablename__ = "clubs"

    id         = Column(Integer, primary_key=True)
    name       = Column(String(100), nullable=False)
    city       = Column(String(100))
    country    = Column(String(100), default="India")
    created_at = Column(DateTime, server_default=func.now())

    teams   = relationship("Team", back_populates="club")
    players = relationship("Player", back_populates="club")
    seasons = relationship("Season", back_populates="club")


class Team(Base):
    __tablename__ = "teams"

    id         = Column(Integer, primary_key=True)
    club_id    = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    name       = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    club    = relationship("Club", back_populates="teams")
    matches = relationship("Match", back_populates="team")


class Season(Base):
    __tablename__ = "seasons"

    id         = Column(Integer, primary_key=True)
    club_id    = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    label      = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date   = Column(Date, nullable=False)
    is_active  = Column(Boolean, default=True)

    club = relationship("Club", back_populates="seasons")


class Player(Base):
    __tablename__ = "players"

    id                 = Column(Integer, primary_key=True)
    club_id            = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    name               = Column(String(100), nullable=False)
    date_of_birth      = Column(Date)
    nationality        = Column(String(100))
    broad_position     = Column(String(10), nullable=False)
    specific_position  = Column(String(10), nullable=False)
    secondary_position = Column(String(10))
    jersey_number      = Column(Integer)
    is_active          = Column(Boolean, default=True)
    created_at         = Column(DateTime, server_default=func.now())

    club = relationship("Club", back_populates="players")


class Match(Base):
    __tablename__ = "matches"

    id             = Column(Integer, primary_key=True)
    team_id        = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    season_id      = Column(Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    opponent_name  = Column(String(100), nullable=False)
    match_date     = Column(Date, nullable=False)
    venue          = Column(String(20))
    goals_scored   = Column(Integer)
    goals_conceded = Column(Integer)
    result         = Column(String(1))
    formation_used = Column(String(10))
    notes          = Column(Text)
    created_at     = Column(DateTime, server_default=func.now())

    team               = relationship("Team", back_populates="matches")
    opposition_profile = relationship("OppositionProfile", back_populates="match", uselist=False)


class PlayerMatchSnapshot(Base):
    __tablename__ = "player_match_snapshots"

    id                = Column(Integer, primary_key=True)
    player_id         = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    match_id          = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    season_id         = Column(Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    minutes_played    = Column(Integer, default=0)
    was_starter       = Column(Boolean, default=True)
    fitness_score     = Column(Float, default=1.0)
    goals             = Column(Integer, default=0)
    assists           = Column(Integer, default=0)
    shots             = Column(Integer, default=0)
    key_passes        = Column(Integer, default=0)
    passes_completed  = Column(Integer, default=0)
    passes_attempted  = Column(Integer, default=0)
    tackles           = Column(Integer, default=0)
    interceptions     = Column(Integer, default=0)
    defensive_errors  = Column(Integer, default=0)
    saves             = Column(Integer, default=0)
    match_rating      = Column(Float)
    pis_snapshot      = Column(Float)
    aerial_duels_won        = Column(Integer, default=0)
    aerial_duels_attempted  = Column(Integer, default=0)
    avg_position_x          = Column(Float, nullable=True)
    avg_position_y          = Column(Float, nullable=True)
    shot_locations          = Column(JSONB, default=list)
    fouls_committed         = Column(Integer, default=0)

    __table_args__ = (UniqueConstraint("player_id", "match_id"),)


class PlayerSeasonStats(Base):
    __tablename__ = "player_season_stats"

    id                 = Column(Integer, primary_key=True)
    player_id          = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    season_id          = Column(Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    team_id            = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    matches_played     = Column(Integer, default=0)
    minutes_played     = Column(Integer, default=0)
    goals              = Column(Integer, default=0)
    assists            = Column(Integer, default=0)
    shots              = Column(Integer, default=0)
    shots_on_target    = Column(Integer, default=0)
    chances_created    = Column(Integer, default=0)
    dribbles_completed = Column(Integer, default=0)
    key_passes         = Column(Integer, default=0)
    passes_completed   = Column(Integer, default=0)
    passes_attempted   = Column(Integer, default=0)
    crosses            = Column(Integer, default=0)
    tackles            = Column(Integer, default=0)
    interceptions      = Column(Integer, default=0)
    blocks             = Column(Integer, default=0)
    clearances         = Column(Integer, default=0)
    aerial_duels_won   = Column(Integer, default=0)
    aerial_duels_total = Column(Integer, default=0)
    defensive_errors   = Column(Integer, default=0)
    saves              = Column(Integer, default=0)
    clean_sheets       = Column(Integer, default=0)
    goals_conceded     = Column(Integer, default=0)

    __table_args__ = (UniqueConstraint("player_id", "season_id"),)


class PlayerPhysicalAttributes(Base):
    __tablename__ = "player_physical_attributes"

    id                    = Column(Integer, primary_key=True)
    player_id             = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    season_id             = Column(Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    height_cm             = Column(Float, nullable=True)
    weight_kg             = Column(Float, nullable=True)
    beep_test_level       = Column(Float, nullable=True)   # e.g. 12.4
    sprint_time_20m       = Column(Float, nullable=True)   # seconds, lower is better
    vertical_jump_cm      = Column(Float, nullable=True)
    date_assessed         = Column(String, nullable=True)
    created_at            = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("player_id", "season_id", name="uq_player_season_physical"),
    )


class PlayerPositionalAnswers(Base):
    __tablename__ = "player_positional_answers"

    id          = Column(Integer, primary_key=True)
    player_id   = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    season_id   = Column(Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    position    = Column(String(10), nullable=False)   # specific position this answer set is for
    answers     = Column(JSONB, default=dict)          # question_key → answer
    created_at  = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("player_id", "season_id", "position", name="uq_player_season_position_answers"),
    )


class PlayerAttributeProfile(Base):
    __tablename__ = "player_attribute_profiles"

    id               = Column(Integer, primary_key=True)
    player_id        = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    season_id        = Column(Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    # Physical — 1 to 20
    pace             = Column(Float, nullable=True)
    acceleration     = Column(Float, nullable=True)
    stamina          = Column(Float, nullable=True)
    strength         = Column(Float, nullable=True)
    jumping          = Column(Float, nullable=True)
    # Technical — 1 to 20
    finishing        = Column(Float, nullable=True)
    passing          = Column(Float, nullable=True)
    crossing         = Column(Float, nullable=True)
    dribbling        = Column(Float, nullable=True)
    heading          = Column(Float, nullable=True)
    long_shots       = Column(Float, nullable=True)
    creativity       = Column(Float, nullable=True)
    # Defensive — 1 to 20
    tackling         = Column(Float, nullable=True)
    positioning      = Column(Float, nullable=True)
    interceptions    = Column(Float, nullable=True)
    aggression       = Column(Float, nullable=True)
    # Mental — 1 to 20
    work_rate        = Column(Float, nullable=True)
    decision_making  = Column(Float, nullable=True)
    # Overall role ratings — 1 to 20
    role_rating      = Column(Float, nullable=True)   # rating for their primary position
    overall_rating   = Column(Float, nullable=True)   # squad-normalised overall
    updated_at       = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("player_id", "season_id", name="uq_player_season_profile"),
    )


class OppositionProfile(Base):
    __tablename__ = "opposition_profiles"

    id                 = Column(Integer, primary_key=True)
    match_id           = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, unique=True)
    opponent_name      = Column(String(100), nullable=False)
    likely_formation   = Column(String(10))
    press_style        = Column(String(20))
    defensive_line     = Column(String(10))
    playing_style      = Column(String(30))
    set_piece_threat   = Column(String(10))
    attributes         = Column(JSONB, default=dict)
    raw_scouting_notes = Column(Text)
    created_at         = Column(DateTime, server_default=func.now())
    match = relationship("Match", back_populates="opposition_profile")

class MatchTeamStats(Base):
    __tablename__ = "match_team_stats"

    id                   = Column(Integer, primary_key=True, index=True)
    match_id             = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    team_id              = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    possession_pct       = Column(Float, nullable=True)
    total_pressures      = Column(Integer, default=0)
    avg_transition_time  = Column(Float, nullable=True)
    defensive_line_height = Column(Float, nullable=True)
    created_at           = Column(DateTime, default=datetime.utcnow)