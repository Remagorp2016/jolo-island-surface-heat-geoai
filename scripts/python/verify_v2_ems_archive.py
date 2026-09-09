"""Integrity checks for frozen Version 2 EMS manuscript-supporting outputs."""
from pathlib import Path
import json
import math
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "results" / "v2_ems"
STRESS = V2 / "stress_tests"
MATCHED = V2 / "matched_transfer"

EXPECTED = {
    "canonical_random_r2": 0.729,
    "canonical_3km_r2": 0.706,
    "canonical_5km_r2": 0.686,
    "canonical_lomo_r2": 0.669,
    "stress_lgbm_3km_r2": 0.7041767059926909,
    "stress_xgb_3km_r2": 0.7031727360760247,
    "stress_rf_3km_r2": 0.7002813198104272,
    "stress_no_elevation_r2": 0.6311149697177063,
    "stress_no_elevation_ndvi_r2": 0.613295625340263,
}


def near(a, b, tol=5e-4):
    return math.isfinite(float(a)) and abs(float(a) - float(b)) <= tol


def main():
    failures = []
    cm = pd.read_csv(STRESS / "V2_CrossModel_3km_Performance.csv").set_index("model")
    ab = pd.read_csv(STRESS / "V2_Ablation_ExplanationStability_Summary.csv").set_index("configuration")
    bo = pd.read_csv(STRESS / "V2_BlockOrigin_Sensitivity_Summary.csv")

    checks = {
        "stress_lgbm_3km_r2": cm.loc["LightGBM", "R2"],
        "stress_xgb_3km_r2": cm.loc["XGBoost", "R2"],
        "stress_rf_3km_r2": cm.loc["RandomForest", "R2"],
        "stress_no_elevation_r2": ab.loc["without_elevation", "R2"],
        "stress_no_elevation_ndvi_r2": ab.loc["without_elevation_and_NDVI", "R2"],
    }
    for k, got in checks.items():
        if not near(got, EXPECTED[k], 1e-10):
            failures.append(f"{k}: expected {EXPECTED[k]}, got {got}")

    if bo["Kendall_W"].min() < 0.96:
        failures.append("Block-origin Kendall W fell below the frozen manuscript bound (0.96).")

    # Optional headline matched-transfer checks if those files are present.
    p = MATCHED / "V2_Multiscale_ExplanationStability_Summary.csv"
    if p.exists():
        ms = pd.read_csv(p)
        # Source package stores the exact fold-concordance values.
        if "Kendall_W" in ms.columns and float(ms["Kendall_W"].min()) < 0.98:
            failures.append("Multiscale attribution concordance is outside the archived range.")

    status = {"status": "PASS" if not failures else "FAIL", "failures": failures, "checked": checks}
    print(json.dumps(status, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
