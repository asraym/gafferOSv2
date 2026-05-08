import os
import joblib
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder

# Only formations with enough winning examples to train reliably
FORMATION_CANDIDATES = {
    0: "4-3-3",
    1: "4-4-2",
    2: "4-2-3-1",
}

TEAM_METRICS = [
    "offensive_output_index",
    "shot_quality_index",
    "defensive_solidity_index",
    "passing_stability_index",
    "possession_share",
    "discipline_index",
    "defensive_line_height",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH   = os.path.join(SCRIPT_DIR, "statsbomb_features.csv")
PKL_PATH   = os.path.join(SCRIPT_DIR, "formation_recommender.pkl")


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the feature matrix for formation recommendation.
    Uses team metrics, opponent metrics, and matchup diffs.
    No rolling averages — formation choice is about current profile, not trajectory.
    """
    feature_cols = []

    for m in TEAM_METRICS:
        team_col = f"team_{m}"
        opp_col  = f"opp_{m}"
        diff_col = f"diff_{m}"

        if team_col in df.columns:
            feature_cols.append(team_col)
        if opp_col in df.columns:
            feature_cols.append(opp_col)
        if diff_col in df.columns:
            feature_cols.append(diff_col)

    # Interaction features
    for col in ["attack_vs_defense", "shot_quality_vs_defense", "possession_battle"]:
        if col in df.columns:
            feature_cols.append(col)

    # Home advantage matters for formation choice
    if "home_away" in df.columns:
        feature_cols.append("home_away")

    return df[feature_cols], feature_cols


def train():
    print("Loading data...")
    df = pd.read_csv(CSV_PATH)
    print(f"Total rows: {len(df)}")

    # Filter to winning matches only
    wins = df[df["outcome"] == 2].copy()
    print(f"Winning rows: {len(wins)}")

    # Filter to our 3 reliable formations
    wins = wins[wins["formation"].isin(FORMATION_CANDIDATES.keys())].copy()
    print(f"Rows after formation filter: {len(wins)}")
    print("\nFormation distribution in training set:")
    for enc, name in FORMATION_CANDIDATES.items():
        count = len(wins[wins["formation"] == enc])
        print(f"  {name} ({enc}): {count} examples")

    # Build features
    X, feature_names = build_features(wins)
    y_raw = wins["formation"].values

    # Encode labels to 0-based integers for XGBoost
    le = LabelEncoder()
    y  = le.fit_transform(y_raw)
    # le.classes_ will be e.g. [0, 1, 2] → maps to formation encodings

    print(f"\nFeatures: {len(feature_names)}")
    print(f"Label encoding: {dict(zip(range(len(le.classes_)), le.classes_))}")

    # Time-based split — same principle as outcome model
    # wins is already a subset so we split by index position
    split_idx = int(len(wins) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"\nTrain: {len(X_train)} rows | Test: {len(X_test)} rows")

    model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="mlogloss",
        early_stopping_rounds=30,
        random_state=42,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50,
    )

    print("\n--- Classification Report ---")
    y_pred = model.predict(X_test)
    print(classification_report(
        y_test, y_pred,
        target_names=[FORMATION_CANDIDATES[c] for c in le.classes_]
    ))

    # Feature importance
    print("\n--- Top 10 Features ---")
    importances = model.feature_importances_
    ranked = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
    for feat, imp in ranked[:10]:
        print(f"  {feat}: {imp:.4f}")

    # Save artifact
    artifact = {
        "model":               model,
        "feature_names":       feature_names,
        "label_encoder":       le,
        "formation_candidates": FORMATION_CANDIDATES,
        "team_metrics":        TEAM_METRICS,
    }
    joblib.dump(artifact, PKL_PATH)
    print(f"\nSaved to {PKL_PATH}")


if __name__ == "__main__":
    train()