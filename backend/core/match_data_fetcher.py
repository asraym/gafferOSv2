from sqlalchemy.orm import Session
from db.models import (
    Match, Player, PlayerMatchSnapshot, PlayerSeasonStats,
    OppositionProfile, MatchTeamStats, Season
)


class MatchDataFetcher:
    """
    Pulls everything the tactical engine needs from the DB for a given match.
    Returns a structured dict — all downstream modules read from this.
    """

    def fetch(self, db: Session, match_id: int, team_id: int) -> dict:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise ValueError(f"Match {match_id} not found.")

        active_season = db.query(Season).filter(Season.is_active == True).first()
        if not active_season:
            raise ValueError("No active season found.")

        players = self._fetch_squad(db, team_id, active_season.id)
        snapshots = self._fetch_snapshots(db, match_id, [p["player_id"] for p in players])
        opposition = self._fetch_opposition(db, match_id)
        team_stats = self._fetch_team_stats(db, match_id, team_id)

        return {
            "match_id": match_id,
            "team_id": team_id,
            "opponent_name": match.opponent_name,
            "home_away": match.venue,         # 'home', 'away', 'neutral'
            "match_date": str(match.match_date),
            "players": players,               # list of player dicts with season stats
            "snapshots": snapshots,           # list of recent match snapshot dicts
            "opposition": opposition,         # parsed opposition profile or None
            "team_stats": team_stats,         # match_team_stats row or None
        }

    def _fetch_squad(self, db: Session, team_id: int, season_id: int) -> list:
        rows = (
            db.query(Player, PlayerSeasonStats)
            .join(PlayerSeasonStats, PlayerSeasonStats.player_id == Player.id)
            .filter(
                PlayerSeasonStats.team_id == team_id,
                PlayerSeasonStats.season_id == season_id,
            )
            .all()
        )
        result = []
        for player, stats in rows:
            result.append({
                "player_id": player.id,
                "name": player.name,
                "broad_position": player.broad_position,
                "specific_position": player.specific_position,
                "secondary_position": player.secondary_position,
                "jersey_number": player.jersey_number,
                # Season cumulative stats
                "season_goals": stats.goals or 0,
                "season_assists": stats.assists or 0,
                "season_shots": stats.shots or 0,
                "season_key_passes": stats.key_passes or 0,
                "season_passes_completed": stats.passes_completed or 0,
                "season_passes_attempted": stats.passes_attempted or 0,
                "season_tackles": stats.tackles or 0,
                "season_interceptions": stats.interceptions or 0,
                "season_defensive_errors": stats.defensive_errors or 0,
                "season_saves": stats.saves or 0,
                "season_matches_played": stats.matches_played or 0,
            })
        return result

    def _fetch_snapshots(self, db: Session, match_id: int, player_ids: list) -> list:
        """
        Returns the most recent 5 snapshots per player (form curve).
        Only includes players who have at least one snapshot.
        """
        if not player_ids:
            return []

        all_snapshots = (
            db.query(PlayerMatchSnapshot)
            .filter(PlayerMatchSnapshot.player_id.in_(player_ids))
            .order_by(PlayerMatchSnapshot.player_id, PlayerMatchSnapshot.id.desc())
            .all()
        )

        # Group by player, take last 5 per player
        from collections import defaultdict
        grouped = defaultdict(list)
        for snap in all_snapshots:
            if len(grouped[snap.player_id]) < 5:
                grouped[snap.player_id].append({
                    "player_id": snap.player_id,
                    "match_id": snap.match_id,
                    "goals": snap.goals or 0,
                    "assists": snap.assists or 0,
                    "shots": snap.shots or 0,
                    "key_passes": snap.key_passes or 0,
                    "passes_completed": snap.passes_completed or 0,
                    "passes_attempted": snap.passes_attempted or 0,
                    "tackles": snap.tackles or 0,
                    "interceptions": snap.interceptions or 0,
                    "defensive_errors": snap.defensive_errors or 0,
                    "saves": snap.saves or 0,
                    "minutes_played": snap.minutes_played or 0,
                    "was_starter": snap.was_starter or False,
                    "fouls_committed": snap.fouls_committed or 0,
                    "aerial_duels_won": snap.aerial_duels_won or 0,
                    "aerial_duels_attempted": snap.aerial_duels_attempted or 0,
                })

        # Flatten back to list
        result = []
        for snaps in grouped.values():
            result.extend(snaps)
        return result

    def _fetch_opposition(self, db: Session, match_id: int):
        profile = (
            db.query(OppositionProfile)
            .filter(OppositionProfile.match_id == match_id)
            .first()
        )
        if not profile:
            return None
        return {
            "opponent_name": profile.opponent_name,
            "formation": profile.likely_formation,
            "press_style": profile.press_style,
            "defensive_line": profile.defensive_line,
            "playing_style": profile.playing_style,
            "set_piece_threat": profile.set_piece_threat,
            "attributes": profile.attributes or {},
        }

    def _fetch_team_stats(self, db: Session, match_id: int, team_id: int):
        row = (
            db.query(MatchTeamStats)
            .filter(
                MatchTeamStats.match_id == match_id,
                MatchTeamStats.team_id == team_id,
            )
            .first()
        )
        if not row:
            return None
        return {
            "possession_pct": row.possession_pct,
            "total_pressures": row.total_pressures or 0,
            "avg_transition_time": row.avg_transition_time,
            "defensive_line_height": row.defensive_line_height,
        }