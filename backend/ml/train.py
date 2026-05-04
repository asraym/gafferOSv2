import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix
from xgboost import XGBClassifier

ROLLING_WINDOW = 5

TEAM_METRICS = [
    "offensive_output_index",
    "shot_quality_index",
    "defensive_solidity_index",
    "passing_stability_index",
    "possession_share",
    "discipline_index",
    "defensive_line_height",
]


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 5-match rolling averages per team sorted chronologically.
    NaNs filled with current match value instead of dropping rows.
    """
    df = df.copy()
    df['match_date'] = pd.to_datetime(df['match_date'])
    df = df.sort_values(['team', 'match_date']).reset_index(drop=True)

    for metric in TEAM_METRICS:
        col = f"team_{metric}"
        roll_col = f"roll_{metric}"
        rolled = (
            df.groupby('team')[col]
            .transform(lambda x: x.shift(1).rolling(ROLLING_WINDOW, min_periods=1).mean())
        )
        # Fill NaN with current match value — no data lost
        df[roll_col] = rolled.fillna(df[col])

    return df


def add_diff_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add team vs opponent mismatch features.
    These capture the actual contest, not just individual team quality.
    """
    df = df.copy()
    for metric in TEAM_METRICS:
        team_col = f"team_{metric}"
        opp_col  = f"opp_{metric}"
        if team_col in df.columns and opp_col in df.columns:
            df[f"diff_{metric}"] = df[team_col] - df[opp_col]

    # Key matchup interactions
    df["attack_vs_defense"] = (
        df["team_offensive_output_index"] - df["opp_defensive_solidity_index"]
    )
    df["shot_quality_vs_defense"] = (
        df["team_shot_quality_index"] - df["opp_defensive_solidity_index"]
    )
    df["possession_battle"] = (
        df["team_possession_share"] - df["opp_possession_share"]
    )

    return df


def build_feature_list() -> list:
    """Define the full feature set for the model."""
    # Raw team and opponent metrics
    team_features = [f"team_{m}" for m in TEAM_METRICS]
    opp_features  = [f"opp_{m}"  for m in TEAM_METRICS]

    # Rolling form features
    roll_features = [f"roll_{m}" for m in TEAM_METRICS]

    # Diff and interaction features
    diff_features = [f"diff_{m}" for m in TEAM_METRICS]
    interaction_features = [
        "attack_vs_defense",
        "shot_quality_vs_defense",
        "possession_battle",
    ]

    # Home advantage
    context_features = ["home_away"]

    return (
        team_features +
        opp_features +
        roll_features +
        diff_features +
        interaction_features +
        context_features
    )


def time_based_split(df: pd.DataFrame, test_ratio: float = 0.2):
    """
    Split by date — train on past, test on future.
    Prevents data leakage from rolling features.
    """
    df = df.sort_values('match_date').reset_index(drop=True)
    split_idx = int(len(df) * (1 - test_ratio))
    split_date = df.iloc[split_idx]['match_date']

    train = df[df['match_date'] < split_date].reset_index(drop=True)
    test  = df[df['match_date'] >= split_date].reset_index(drop=True)

    print(f"  Train: {len(train)} rows up to {train['match_date'].max().date()}")
    print(f"  Test:  {len(test)} rows from {test['match_date'].min().date()}")

    return train, test


def train():
    print("Loading data...")
    df = pd.read_csv("ml/statsbomb_features.csv")
    print(f"  {len(df)} rows loaded")

    print("\nAdding rolling form features...")
    df = add_rolling_features(df)

    print("Adding diff and interaction features...")
    df = add_diff_features(df)

    feature_names = build_feature_list()
    print(f"  Total features: {len(feature_names)}")

    print("\nTime-based train/test split (80/20 by date)...")
    train_df, test_df = time_based_split(df)

    X_train = train_df[feature_names].values
    y_train = train_df['outcome'].values
    X_test  = test_df[feature_names].values
    y_test  = test_df['outcome'].values

    print(f"\nOutcome distribution:")
    print(f"  Train — {dict(zip(*np.unique(y_train, return_counts=True)))}")
    print(f"  Test  — {dict(zip(*np.unique(y_test, return_counts=True)))}")

    print("\nTraining XGBoost...")
    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='mlogloss',
        early_stopping_rounds=30,
        random_state=42,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50,
    )

    print("\nEvaluating...")
    y_pred = model.predict(X_test)

    print("\nClassification Report:")
    print(classification_report(
        y_test, y_pred,
        target_names=["Loss", "Draw", "Win"]
    ))

    print("Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"              Pred Loss  Pred Draw  Pred Win")
    print(f"  Actual Loss   {cm[0][0]:<9}  {cm[0][1]:<9}  {cm[0][2]}")
    print(f"  Actual Draw   {cm[1][0]:<9}  {cm[1][1]:<9}  {cm[1][2]}")
    print(f"  Actual Win    {cm[2][0]:<9}  {cm[2][1]:<9}  {cm[2][2]}")

    print("\nFeature Importance (top 15):")
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    for _, row in importance_df.head(15).iterrows():
        bar = "█" * int(row['importance'] * 200)
        print(f"  {row['feature']:<45} {row['importance']:.4f}  {bar}")

    print("\nSaving model...")
    joblib.dump({
        'model': model,
        'feature_names': feature_names,
        'team_metrics': TEAM_METRICS,
    }, "ml/match_predictor.pkl")
    print("  Saved to ml/match_predictor.pkl")

    return model, feature_names


if __name__ == "__main__":
    train()