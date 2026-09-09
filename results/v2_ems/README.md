# Version 2 EMS reproducibility layer

This directory contains the frozen outputs supporting the Version 2 manuscript:

**Prediction-Attribution Transfer in Environmental GeoAI: Matched Geographic Validation of Surface Heat**

Target journal: *Environmental Modelling & Software*.

## Why Version 2 exists

Version 1 established the Jolo Island surface-heat modelling baseline. Version 2 changes the methodological emphasis from a case-study explanation of land-surface temperature to a validation question: **do prediction and feature attribution transfer in the same way when geography is withheld?**

The Version 2 archive therefore separates:

1. **predictive transferability** — R², RMSE and MAE under random, spatial-block and municipality-held-out validation; and
2. **attribution transferability** — SHAP rank and direction stability recalculated from models retrained under the same geographic exclusions.

## Directory contents

- `matched_transfer/` — multiscale fold-wise SHAP stability, municipality-held-out attribution transfer, environmental-support diagnostics, seasonal attribution stability, seed sensitivity, and supporting summary tables.
- `stress_tests/` — like-for-like 3-km robustness reruns for block-origin shifts, model-family substitution, and dominant-predictor ablation.
- `../../scripts/python/run_v2_ems_stress_tests.py` — rerun implementation for the matched-transfer and EMS stress-test workflow. It writes to `reproduced_results/v2_ems/` and never overwrites the frozen tables.
- `../../scripts/python/verify_v2_ems_archive.py` — integrity checks for manuscript headline values.

Two large sample-level diagnostic tables are kept in the complete release archive rather than duplicated as unpacked GitHub CSVs:

- `V2_LOMO_AOA_SampleDiagnostics.csv`
- `V2_SHAP_HeatDriver_Regimes_Samples.csv`

They are contained in `releases/Jolo_V2_MatchedTransfer_CompleteOutputs.zip`.

## Canonical versus dedicated stress-test values

The manuscript deliberately distinguishes the **canonical benchmark** from the dedicated Version 2 stress-test rerun.

Canonical LightGBM benchmark:

- random five-fold CV R² = 0.729
- 3-km blocked CV R² = 0.706
- 5-km blocked CV R² = 0.686
- leave-one-municipality-out pooled R² = 0.669

Dedicated like-for-like 3-km stress-test reference:

- LightGBM R² = 0.704176706; RMSE = 1.238367977 °C; MAE = 0.954295374 °C

The stress-test value is used only when comparing block origins, algorithms, and ablations under the same rerun protocol; it does not replace the canonical benchmark.

## Headline robustness checks

### Spatial-block origin

Shifting the 3-km grid by half a block in x, y, or both changed R² from 0.7042 to as low as 0.6918, while Kendall's W for attribution ranks remained 0.9627–0.9920.

### Tree algorithm

Under the common 3-km design:

- LightGBM R² = 0.7042
- XGBoost R² = 0.7032
- Random forest R² = 0.7003

Within-model attribution concordance remained high (W approximately 0.987–0.995), and the mean predictor ranking was identical across the three tree ensembles in the frozen analysis.

### Dominant-predictor ablation

- Full set: R² = 0.7042; W = 0.9920
- Without elevation: R² = 0.6311; W = 0.9924
- Without elevation and NDVI: R² = 0.6133; W = 0.9886

Thus attribution-rank stability is not solely an artifact of one dominant predictor anchoring the ordering.

## Matched geographic attribution transfer

The frozen Version 2 analyses report:

- fold-wise attribution rank W = 1.000 at 1, 2, and 3 km and W = 0.9848 at 5 km;
- municipality-held-out attribution concordance W = 0.945 in the manuscript analysis;
- municipality prediction R² ranging from -0.437 (Jolo; n = 31) to 0.774 (Patikul), while rank similarity to the full-island model remains mostly 0.95–1.00;
- Spearman association between municipality R² and attribution-rank similarity ρ = 0.085, p = 0.803;
- seasonal mean pairwise fold-rank correlations of 0.990 (MAM), 0.986 (JJA), and 0.950 (DJF);
- 10 LightGBM seeds yielding identical global attribution rank order (W = 1.000).

## Environmental support and residual limitations

The spatial-CV-calibrated environmental-support threshold is DI = 1.890. Approximately 91.6% of municipality-held-out samples lie inside the supported predictor domain. This diagnostic does not fully explain geographic prediction error.

The manuscript also reports significant residual spatial structure (Moran's I = 0.530; permutation p = 0.005). Stable attribution must therefore be interpreted as **reproducibility of the fitted model's attribution structure**, not causal truth or complete physical explanation.

## Reproduction

From the repository root:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python scripts/python/run_v2_ems_stress_tests.py
python scripts/python/verify_v2_ems_archive.py
```

The analysis-ready datasets already distributed under `data/derived/` are used as inputs. Raw upstream Earth-observation archives are not redistributed.
