#!/usr/bin/env python3
"""Log the selected VMD 4-shard results to local MLflow.

This script backfills tracking from already recovered CSV/PNG artifacts.
It does not rerun the model.
"""
from pathlib import Path
import json
import pandas as pd

try:
    import mlflow
except ImportError as exc:
    raise SystemExit("mlflow is required. Install from requirements.txt") from exc

ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "outputs" / "tables" / "vmd"
FIG_DIR = ROOT / "outputs" / "figures" / "vmd"
TRACK_DIR = ROOT / "mlruns"

mlflow.set_tracking_uri(TRACK_DIR.as_uri())
mlflow.set_experiment("vmd_selected125")
summary = pd.read_csv(TABLE_DIR / "summary.csv").sort_values("wape")

for _, row in summary.iterrows():
    run_name = str(row["run"])
    with mlflow.start_run(run_name=run_name):
        mlflow.set_tag("model", "team_vmd_garch_lstm")
        mlflow.set_tag("feature_set", "selected125")
        mlflow.set_tag("folds", "28")
        mlflow.set_tag("source", "team_vmd_4shard_backfill")
        for key, value in row.items():
            if key in {"rank", "run", "params_json"}:
                continue
            try:
                mlflow.log_metric(key, float(value))
            except Exception:
                pass
        if "params_json" in row and isinstance(row["params_json"], str):
            try:
                params = json.loads(row["params_json"])
                for k, v in params.items():
                    mlflow.log_param(k, v)
            except Exception:
                pass
        for artifact in ["summary.csv", "by_fold.csv", "report.md"]:
            path = TABLE_DIR / artifact
            if path.exists():
                mlflow.log_artifact(str(path), artifact_path="tables")
        if run_name == summary.iloc[0]["run"]:
            pred = TABLE_DIR / "pred.csv"
            if pred.exists():
                mlflow.log_artifact(str(pred), artifact_path="tables")
            for fig in FIG_DIR.glob("*.png"):
                mlflow.log_artifact(str(fig), artifact_path="figures")
print(f"logged {len(summary)} VMD runs to {TRACK_DIR}")
