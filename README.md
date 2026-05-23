# GafferOS v2

AI-assisted tactical decision support system for semi-professional football clubs. Built for teams at Indian 2nd/3rd division level who have no access to expensive analytics platforms.

The system processes match footage, builds rich player profiles automatically, and gives coaches context-aware tactical recommendations before each match.

---

## What It Does

- Watches match footage via a CV/YOLO pipeline and extracts player and team stats automatically
- Builds season-long player profiles with physical attributes, positional traits, and form curves
- Parses coach scouting notes into structured opposition profiles using NLP
- Runs an XGBoost model trained on StatsBomb open data to output win/draw/loss probabilities
- Recommends formation, press intensity, defensive line, and tactical focus based on squad traits, player attributes, and opposition analysis
- Detects player linkup pairs and derives out-of-possession defensive shape from squad trait profiles
- Flags rotation risks, positional mismatches, and outlier performers

---

## Tech Stack

**Backend**
- Python 3.14, FastAPI, Uvicorn
- PostgreSQL, SQLAlchemy
- XGBoost, Scikit-learn, Joblib
- Pydantic, Pandas, NumPy

**Frontend**
- Next.js 14, TypeScript, App Router
- CSS Modules, Framer Motion, Lenis
- SVG formation pitch with animated transitions

**Infrastructure**
- Deployed on Render (backend + database)
- PostgreSQL free tier (Render)
- GitHub for version control

---

## Architecture

```
CV/YOLO Pipeline (partner)
        ↓
PostgreSQL Database
        ↓
FastAPI Backend
  ├── MatchDataFetcher       — pulls squad, snapshots, opposition from DB
  ├── PlayerRanker           — form scores, fatigue, tactical profiles
  ├── TeamMetricCalculator   — 7 model metrics (shared with training)
  ├── MatchupLayer           — cross-references opposition vs squad attributes
  ├── TacticalReasoner       — XGBoost inference + formation + press/line/focus
  ├── SquadTraitAggregator   — linkup pairs + defensive shape from traits
  ├── TacticalStyle          — squad style vector derivation
  ├── TacticalConstraints    — hard constraint validation + coherence scoring
  └── Explainer              — plain English reasoning report
        ↓
Next.js Frontend
  ├── Squad management
  ├── Opposition scouting
  ├── Animated formation pitch (attack/defense toggle)
  └── Full tactical report
```

---

## ML Model

- **Algorithm:** XGBoost with class weighting
- **Training data:** StatsBomb open data — La Liga, Champions League, Premier League, Ligue 1, Bundesliga (1104 rows, 552 matches)
- **Features:** 35 — team metrics × 7, opponent metrics × 7, rolling averages × 7, matchup differentials × 7, 3 interaction features, home/away
- **Results:** 75% overall accuracy, Win F1: 83%, Loss F1: 83%, Draw F1: 16%
- **Top feature:** `diff_defensive_solidity_index` — defensive mismatch is the biggest predictor
- **Split:** Time-based 80/20 — no data leakage

---

## Player Profile System

Each player has two layers:

- **Season profile** — cumulative stats over the full season extracted by CV pipeline
- **Form curve** — last N match snapshots showing recent trajectory

Physical attributes (beep test, sprint time, vertical jump, height, weight) are converted to Football Manager-style 1–20 ratings. Combined with CV stats to produce role-specific ratings and an overall rating.

Coaches assign positional traits from a bank of 150+ traits across 9 position groups. Traits drive formation selection, press decisions, linkup pair detection, and the plain English reasoning report.

---

## Formation Pitch

The analysis page features an animated SVG formation pitch:

- Horizontal landscape layout
- Auto-cycles between attacking formation and defensive shape every 3 seconds
- Toggle to lock either state
- Linkup pair lines drawn between connected players in attack mode
- Outlier highlighting — up to 3 players flagged (in form / form dip / weak link)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/players/register` | Register single player |
| POST | `/api/players/import-csv` | Bulk import squad from CSV |
| POST | `/api/players/physical-csv` | Bulk upload physical test data |
| GET | `/api/players?team_id=1` | Squad overview with ratings and traits |
| GET | `/api/players/{id}/form` | Last N match snapshots |
| POST | `/api/players/{id}/traits` | Save coach-assigned traits |
| POST | `/api/players/{id}/physical` | Single player physical assessment |
| POST | `/api/matches/register` | Register upcoming fixture |
| POST | `/api/matches/snapshot` | CV pipeline writes per-player stats |
| GET | `/api/matches/upcoming` | Next unplayed match |
| POST | `/api/matches/analyse` | Full tactical report |
| POST | `/api/matches/feedback` | Store actual result post-match |
| POST | `/api/opposition/parse` | Parse scouting notes into structured data |

Live API docs: https://gafferosv2.onrender.com/docs

---

## Running Locally

### Backend
```bash
cd D:\gafferOS\v2\backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd D:\gafferOS\v2\frontend\react
npm run dev
```

API docs: http://localhost:8000/docs  
Frontend: http://localhost:3000

### Regenerate ML model
```bash
python ml/feature_engineering.py   # ~45 mins
python ml/train.py                  # ~30 seconds
```

---

## Project Status

| Component | Status |
|-----------|--------|
| Database schema | ✅ Complete |
| Player registration + CSV import | ✅ Complete |
| Physical assessment (single + bulk) | ✅ Complete |
| Opposition parser | ✅ Complete |
| CV pipeline ingestion | ✅ Complete |
| ML training pipeline | ✅ Complete |
| Tactical engine (all layers) | ✅ Complete |
| Player trait system | ✅ Complete |
| Attribute calculator | ✅ Complete |
| Matchup layer | ✅ Complete |
| Squad trait aggregator + linkup pairs | ✅ Complete |
| Defensive shape + formation | ✅ Complete |
| Feedback loop | ✅ Complete |
| Deployment (Render) | ✅ Complete |
| React frontend | ✅ Complete |
| Auth / multi-club support | 🔄 Planned |
| Season management endpoints | 🔄 Planned |

---

## Two-Man Team

- **Partner** — CV/YOLO pipeline. Processes match footage, extracts player and team stats, writes to the shared database.
- **Me** — Everything from the data layer onwards. Player profiles, tactical engine, opposition parser, API, frontend.

Handoff point: `player_match_snapshots` table.

---

## Feedback Loop

Every analysis call automatically stores the recommendation. After each match, coaches submit the actual result via `/matches/feedback`. At 100+ matches with `coach_followed_rec = true`, `ml/train_tactical.py` will retrain on real club data.

---

Built for the game.

Active development — transitioning from a prediction-focused system into a full tactical decision-support platform.
