import pandas as pd
import numpy as np

df = pd.read_csv("ml/statsbomb_features.csv")

TEAM_METRICS = [
    "team_offensive_output_index",
    "team_shot_quality_index",
    "team_defensive_solidity_index",
    "team_aerial_dominance_index",
    "team_press_intensity_index",
    "team_passing_stability_index",
    "team_possession_share",
    "team_transition_speed_index",
    "team_defensive_line_height",
    "team_match_performance_score",
    "team_discipline_index",
    "team_chance_creation_rate",
]

OUTCOME_LABELS = {0: "Loss", 1: "Draw", 2: "Win"}

# ── 1. Basic info ─────────────────────────────────────────────────────────────
print("=" * 60)
print("1. BASIC INFO")
print("=" * 60)
print(f"Total rows    : {len(df)}")
print(f"Total columns : {len(df.columns)}")
print(f"Date range    : {df['match_date'].min()} → {df['match_date'].max()}")
print(f"\nOutcome distribution:")
for k, v in df['outcome'].value_counts().sort_index().items():
    print(f"  {OUTCOME_LABELS[k]:<6} ({k}): {v} rows ({v/len(df)*100:.1f}%)")

# ── 2. Null check ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("2. NULL CHECK")
print("=" * 60)
nulls = df.isnull().sum()
nulls = nulls[nulls > 0]
if len(nulls) == 0:
    print("  No nulls found — clean.")
else:
    print(nulls)

# ── 3. Metric means by outcome ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("3. METRIC MEANS BY OUTCOME")
print("=" * 60)
grouped = df.groupby('outcome')[TEAM_METRICS].mean().round(3)
grouped.index = [OUTCOME_LABELS[i] for i in grouped.index]
print(grouped.T.to_string())

# ── 4. Win vs Loss delta — most predictive metrics at top ─────────────────────
print("\n" + "=" * 60)
print("4. WIN vs LOSS DELTA (sorted by predictive power)")
print("=" * 60)
wins   = df[df['outcome'] == 2][TEAM_METRICS].mean()
losses = df[df['outcome'] == 0][TEAM_METRICS].mean()
diff   = (wins - losses).round(3).sort_values(ascending=False)
for metric, delta in diff.items():
    short = metric.replace("team_", "")
    bar = "█" * int(abs(delta) * 40)
    direction = "+" if delta > 0 else "-"
    print(f"  {short:<35} {direction}{abs(delta):.3f}  {bar}")

# ── 5. Cap check — how often metrics hit 1.0 ─────────────────────────────────
print("\n" + "=" * 60)
print("5. CAP CHECK (% of values at 1.0)")
print("=" * 60)
for col in TEAM_METRICS:
    pct = (df[col] == 1.0).sum() / len(df) * 100
    status = "⚠ WARNING" if pct > 10 else "OK"
    print(f"  {status:<12} {col.replace('team_', ''):<35} {pct:.1f}%")

# ── 6. Percentile distribution ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("6. PERCENTILE DISTRIBUTION")
print("=" * 60)
pcts = df[TEAM_METRICS].quantile([0.10, 0.25, 0.50, 0.75, 0.90]).round(3)
pcts.index = ["p10", "p25", "p50", "p75", "p90"]
print(pcts.T.to_string())

# ── 7. Correlation matrix ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("7. CORRELATION BETWEEN TEAM METRICS")
print("   (>0.7 means potentially redundant)")
print("=" * 60)
corr = df[TEAM_METRICS].corr().round(2)
# Only print pairs with high correlation to keep it readable
printed = set()
for col1 in TEAM_METRICS:
    for col2 in TEAM_METRICS:
        if col1 == col2:
            continue
        pair = tuple(sorted([col1, col2]))
        if pair in printed:
            continue
        val = corr.loc[col1, col2]
        if abs(val) > 0.5:
            flag = "⚠ HIGH" if abs(val) > 0.7 else "  NOTE"
            c1 = col1.replace("team_", "")
            c2 = col2.replace("team_", "")
            print(f"  {flag}  {c1:<35} ↔  {c2:<35} {val:+.2f}")
        printed.add(pair)

# ── 8. Home advantage ─────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("8. HOME ADVANTAGE")
print("=" * 60)
home = df[df['home_away'] == 1]
away = df[df['home_away'] == 0]
home_wr = len(home[home['outcome'] == 2]) / len(home) * 100
away_wr = len(away[away['outcome'] == 2]) / len(away) * 100
draw_r  = len(df[df['outcome'] == 1]) / len(df) * 100
print(f"  Home win rate : {home_wr:.1f}%")
print(f"  Away win rate : {away_wr:.1f}%")
print(f"  Draw rate     : {draw_r:.1f}%")

# ── 9. Metric ranges summary ──────────────────────────────────────────────────
print("\n" + "=" * 60)
print("9. METRIC RANGES (min / mean / max)")
print("=" * 60)
for col in TEAM_METRICS:
    mn  = df[col].min()
    avg = df[col].mean()
    mx  = df[col].max()
    short = col.replace("team_", "")
    print(f"  {short:<35} {mn:.3f} / {avg:.3f} / {mx:.3f}")

print("\n" + "=" * 60)
print("EDA COMPLETE")
print("=" * 60)