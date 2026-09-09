# Release notes — v2.0.0

## Jolo Island Surface Heat GeoAI: prediction-attribution transfer release

Version 2.0.0 is the reproducibility release accompanying the rebuilt *Environmental Modelling & Software* manuscript, **“Prediction-Attribution Transfer in Environmental GeoAI: Matched Geographic Validation of Surface Heat.”**

### Main methodological change

Version 1 evaluated spatial prediction and reported model explanations. Version 2 explicitly evaluates **prediction transfer and attribution transfer as separate validation targets** by recalculating SHAP explanations from geographically retrained models under the same held-out partitions used for prediction testing.

### New analyses

- fold-wise SHAP attribution stability at 1, 2, 3, and 5 km spatial blocking;
- municipality-held-out prediction and attribution transfer;
- prediction-performance versus attribution-similarity analysis;
- spatial-CV-calibrated environmental-support / Area-of-Applicability diagnostics;
- 3-km block-origin sensitivity using half-block shifts;
- common-fold comparison of LightGBM, XGBoost, and random forest;
- dominant-predictor ablation;
- seasonal matched SHAP stability for MAM, JJA, and DJF;
- LightGBM seed-sensitivity analysis;
- integrity verification of frozen manuscript-supporting outputs.

### Source-of-record distinction

The original Version 1 Zenodo deposit remains immutable. Version 2 adds the new matched-transfer and robustness layer while retaining the frozen Version 1 analysis-ready datasets and canonical benchmarks.

Canonical LightGBM performance remains:

- random CV R² = 0.729
- 3-km blocked CV R² = 0.706
- 5-km blocked CV R² = 0.686
- leave-one-municipality-out pooled R² = 0.669

The dedicated Version 2 3-km stress-test reference is R² = 0.704176706 and is used only for like-for-like robustness comparisons.

### Reproducibility additions

- `scripts/python/run_v2_ems_stress_tests.py`
- `scripts/python/verify_v2_ems_archive.py`
- `results/v2_ems/matched_transfer/`
- `results/v2_ems/stress_tests/`
- compact complete-output archives under `releases/`
- Version 2 Zenodo metadata template under `metadata/`

### Previous archived version

Version 1.0.0: DOI 10.5281/zenodo.22541245
