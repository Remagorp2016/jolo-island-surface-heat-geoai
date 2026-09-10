# Jolo Island Surface Heat GeoAI

Reproducibility repository for the Version 2 study:

**Prediction–Attribution Transfer in Environmental GeoAI: Matched Geographic Validation of Surface Heat**

**Author:** Fadzlur-Nijar A. Adju  
**Affiliation:** College of Computing Studies, Mindanao State University–Sulu, Philippines  
**ORCID:** https://orcid.org/0009-0003-1865-7596  
**Corresponding author:** fadzlur-nijar.adju@msusulu.edu.ph

## Version status

- **Version 1.0.0** preserves the original surface-heat GeoAI reproducibility archive:  
  DOI: **10.5281/zenodo.22541245**
- **Version 2.0.0** extends the project with matched geographic validation of prediction and model-attribution transfer:  
  DOI: **10.5281/zenodo.22668346**

The Version 2 Zenodo record is a complete, self-contained reproducibility archive that preserves the Version 1 baseline while adding the new transferability and robustness analyses.

## Study and methodological contribution

The empirical test bed is a 2013–2026 Landsat 8/9 surface-temperature climatology for Jolo Island, Philippines, represented on a 300 m systematic terrestrial lattice with **n = 8,838** observations.

Predictors represent:

- vegetation condition;
- built/exposed surface characteristics;
- land cover;
- elevation and terrain;
- coastal position; and
- other spatial-environmental characteristics retained in the frozen modelling dataset.

Version 2 addresses a broader environmental-modelling question:

> **Do predictive performance and model attribution transfer in the same way when geography is withheld?**

The study therefore evaluates **prediction transfer** and **attribution transfer** as related but non-equivalent properties of environmental GeoAI.

SHAP values are interpreted as **model attributions**, not causal effects.

## Canonical predictive benchmarks

The frozen core result files provide the following LightGBM performance:

| Validation design | R² |
|---|---:|
| Random five-fold cross-validation | 0.730 |
| 3 km spatial-block cross-validation | 0.704 |
| 5 km spatial-block cross-validation | 0.685 |
| Leave-one-municipality-out transfer | 0.668 |

Exact values are stored in:

- `results/core/Final_RandomCV.csv`
- `results/core/Final_SpatialCV.csv`
- `results/core/Final_MunicipalityHeldOut_Overall.csv`

These frozen result tables are the numerical source of truth for manuscript reporting.

## Matched prediction–attribution transfer

Version 2 evaluates model attribution using geographically retrained models produced under the same spatial exclusions used to evaluate predictive transfer.

Two complementary attribution contexts are retained.

### Held-out geographic context

When SHAP summaries are calculated using each corresponding held-out geographic subset:

- 3 km geographically retrained models show high rank concordance  
  **Kendall's W = 0.992**
- municipality-held-out models remain strongly concordant  
  **Kendall's W = 0.921**

These results quantify attribution reproducibility while allowing both model training geography and attribution-evaluation geography to vary.

### Common-reference context

A complementary stress test compares geographically retrained models under a common attribution-evaluation context.

Results are:

- 3 km retrained models:  
  **Kendall's W = 0.987**
- all 11 municipality-held-out models:  
  **Kendall's W = 0.987**
- municipality subset with n ≥ 100:  
  **Kendall's W = 0.987**

The common-reference analysis therefore indicates that much of the apparent geographic variation in attribution magnitude does not translate into instability of the overall predictor ranking.

Frozen outputs are stored under:

`results/v2_ems/stress_tests/`

The `v2_ems` directory name is retained as historical provenance from the Version 2 development stage and does not indicate a current journal commitment.

## Prediction–attribution decoupling

Municipality-specific predictive performance varies substantially, whereas attribution-rank similarity remains comparatively stable.

The association between municipality-level prediction performance and attribution-rank similarity is weak:

**Spearman ρ = 0.085, p = 0.803**

This supports the central methodological conclusion that predictive transferability and attribution transferability should be evaluated separately.

## Robustness analyses

Version 2 includes several stress tests.

### Spatial-block origin sensitivity

Shifting the 3 km spatial-block origin changed predictive performance while attribution concordance remained high.

Across block-origin configurations:

- R² ranged approximately from **0.692 to 0.704**
- Kendall's W remained approximately **0.963–0.992**

### Cross-algorithm robustness

Under the common 3 km design:

- LightGBM: R² ≈ **0.704**
- XGBoost: R² ≈ **0.703**
- Random Forest: R² ≈ **0.700**

Mean predictor rankings were identical across the three tree-based algorithms in the frozen analysis.

### Dominant-predictor ablation

Removing major predictors substantially reduced predictive performance without materially reducing attribution-rank concordance.

- Full predictor set:  
  R² = **0.704**, W = **0.992**
- Without elevation:  
  R² = **0.631**, W = **0.992**
- Without elevation and NDVI:  
  R² = **0.613**, W = **0.989**

This indicates that the observed attribution stability is not solely an artifact of one dominant predictor anchoring the feature ranking.

### Seasonal robustness

Matched seasonal analyses were conducted for:

- MAM;
- JJA; and
- DJF.

Predictive performance varied seasonally, while the dominant attribution hierarchy remained broadly stable.

### Environmental support

A spatial-CV-calibrated environmental-support diagnostic was used to assess whether geographic transfer failures were primarily associated with unsupported predictor combinations.

Approximately **91.6%** of municipality-held-out observations remained within the empirically supported predictor domain.

### Residual spatial dependence

Significant residual spatial autocorrelation remained:

**Moran's I = 0.530, permutation p = 0.005**

This is retained as an explicit limitation.

Stable attribution therefore means reproducibility of the fitted model's attribution structure under the tested perturbations; it does **not** establish causal truth, physical completeness, or universal transferability.

## Repository structure

```text
.
├── CITATION.cff
├── LICENSE
├── README.md
├── RELEASE_NOTES_v2.0.0.md
├── requirements.txt
├── environment.yml
├── data/
│   ├── boundaries/
│   └── derived/
├── docs/
├── figures/
├── metadata/
│   └── ZENODO_V2_METADATA.md
├── releases/
│   ├── Jolo_V2_MatchedTransfer_CompleteOutputs.zip
│   └── Jolo_V2_StressTests_FrozenOutputs.zip
├── results/
│   ├── core/
│   ├── seasonal/
│   └── v2_ems/
│       ├── matched_transfer/
│       └── stress_tests/
└── scripts/
    ├── gee/
    └── python/
        ├── build_main_sample_from_rasters.py
        ├── run_reproduction.py
        ├── run_v2_ems_stress_tests.py
        └── verify_v2_ems_archive.py
