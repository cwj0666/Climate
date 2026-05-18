#!/usr/bin/env python3
"""Validate selected feature inputs and refresh compact feature tables."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MI = ROOT / "data" / "model_inputs"
ART = ROOT / "outputs" / "tables" / "artifacts"

NON_FEATURE = {
    "trd_dd",
    "future_date_30d",
    "actual_elapsed_days_30d",
    "same_panel_30d",
    "target_logret_30d",
    "future_date_60d",
    "actual_elapsed_days_60d",
    "same_panel_60d",
    "target_logret_60d",
}
BANNED = {"mkt_market_vwap", "mkt_log_market_vwap"}
REQUIRED = {"mkt_vwap_lag1", "mkt_vwap_lag5", "mkt_vwap_lag20", "mkt_vwap_lag60"}
TABLE_COLS = [
    "feature",
    "feature_label_ko",
    "feature_group",
    "source",
    "source_column",
    "asof_rule",
    "selection_status",
]


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    matrix = pd.read_parquet(MI / "selected_feature_matrix.parquet")
    manifest = pd.read_csv(MI / "selected_feature_manifest.csv")

    features = [c for c in matrix.columns if c not in NON_FEATURE]
    missing_required = REQUIRED - set(features)
    banned_present = BANNED & set(features)

    if len(features) != len(manifest):
        raise ValueError(f"feature count mismatch: matrix={len(features)}, manifest={len(manifest)}")
    if banned_present:
        raise ValueError(f"banned target-overlap features present: {sorted(banned_present)}")
    if missing_required:
        raise ValueError(f"required lag features missing: {sorted(missing_required)}")

    cols = [c for c in TABLE_COLS if c in manifest.columns]
    manifest[cols].to_csv(ART / "features.csv", index=False)

    addbacks = manifest[manifest.get("selection_status", "").astype(str).eq("selected_addback")]
    addbacks[[c for c in cols if c in addbacks.columns]].to_csv(ART / "addbacks.csv", index=False)

    label_bad = manifest[
        manifest["feature_label_ko"].isna()
        | (manifest["feature_label_ko"].astype(str) == manifest["feature"].astype(str))
    ]
    label_bad[["feature", "feature_label_ko"]].to_csv(ART / "label_check.csv", index=False)

    print({"features": len(features), "addbacks": len(addbacks), "label_issues": len(label_bad)})


if __name__ == "__main__":
    main()
