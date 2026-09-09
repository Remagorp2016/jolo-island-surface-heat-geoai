# Jolo Island Surface Heat GeoAI

Reproducibility repository for the Version 2 manuscript:

**Prediction-Attribution Transfer in Environmental GeoAI: Matched Geographic Validation of Surface Heat**

**Author:** Fadzlur-Nijar A. Adju  
**Affiliation:** College of Computing Studies, Mindanao State University–Sulu, Philippines  
**ORCID:** https://orcid.org/0009-0003-1865-7596  
**Corresponding author:** fadzlur-nijar.adju@msusulu.edu.ph

## Version status

- **Version 1.0.0** is the immutable original reproducibility archive: DOI **10.5281/zenodo.22541245**.
- **Version 2.0.0** adds the matched prediction-attribution transfer framework and EMS robustness analyses. The GitHub files are prepared for the Version 2 archival release; the new version-specific Zenodo DOI will be added here after the new Zenodo version is published.

## Study and methodological contribution

The empirical test bed is a 2013–2026 Landsat 8/9 surface-temperature climatology for Jolo Island, Philippines, sampled on a 300 m systematic terrestrial lattice (**n = 8,838**). Predictors represent vegetation, built/exposed surfaces, land cover, elevation, terrain orientation, and coastal position.

Version 2 focuses on a broader environmental-modelling problem: **predictive transferability and attribution transferability are not the same property**. SHAP explanations are therefore recalculated independently from models retrained under the same geographic exclusions used to test prediction.

Canonical LightGBM benchmarks are:

- random five-fold CV: **R² = 0.729**
- 3 km spatial-block CV: **R² = 0.706**
- 5 km spatial-block CV: **R² = 0.686**
- leave-one-municipality-out pooled transfer: **R² = 0.669**

Attribution rankings are invariant across 1–3 km held-out folds (Kendall's **W = 1.000**) and remain highly concordant at 5 km (**W = 0.985**). Municipality-held-out prediction skill varies strongly, while attribution-rank similarity remains mostly high; their association is weak (**Spearman ρ = 0.085, p = 0.803**).

Dedicated stress tests further show that attribution concordance remains high under block-origin shifts, tree-algorithm substitution, and removal of dominant predictors even when predictive skill changes materially. Significant residual spatial autocorrelation (**Moran's I = 0.530, p = 0.005**) is retained as an explicit limitation: stable attribution is reproducibility of the fitted model's explanation structure, not causal truth or complete physical explanation.

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
        ├── run_reproduction.py
        ├── run_v2_ems_stress_tests.py
        └── verify_v2_ems_archive.py
```

## Reproduce Version 1 canonical benchmarks

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python scripts/python/run_reproduction.py
```

## Reproduce the Version 2 robustness layer

```bash
python scripts/python/run_v2_ems_stress_tests.py
```

The rerun writes to `reproduced_results/v2_ems/` so that the frozen manuscript-supporting outputs are not overwritten.

Verify the frozen Version 2 archive:

```bash
python scripts/python/verify_v2_ems_archive.py
```

See `results/v2_ems/README.md` for the canonical-versus-stress-test distinction and exact headline values.

## Data notes

`data/derived/Jolo_Modeling_Sample_Local_v03.csv` is the frozen main 300 m modeling sample.

`data/derived/Jolo_Seasonal_Robustness_ModelSample_v04.csv` is the frozen seasonal sample containing MAM, JJA, and DJF response/predictor values and the independently audited 30 m GHSL built fraction.

Longitude and latitude are retained for diagnostics and mapping but are **not** ordinary explanatory predictors. WorldCover is treated categorically and one-hot encoded, with rare classes collapsed to `Other`.

## Software environment

The analysis uses the package versions recorded in `requirements.txt`, including NumPy, pandas, SciPy, scikit-learn, XGBoost, LightGBM, SHAP, statsmodels, GeoPandas, Rasterio, and Matplotlib. Deterministic seeds and fixed model configurations are encoded in the scripts.

## Data availability and DOI

Current archived version:

**Version 1.0.0 — DOI: 10.5281/zenodo.22541245**

A Version 2 Zenodo record will be created as a new version of the same archive. The Version 2 DOI will replace this status note only after Zenodo publishes it.

## Authorship and declarations

**Sole author:** Fadzlur-Nijar A. Adju

**Funding:** This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

**Competing interests:** The author declares no conflict of interest.

**Ethics:** Not applicable. The study uses satellite, gridded geospatial, and administrative-boundary data and involves no human participants, personal data, or animals.

## Licenses

- Analysis code in `scripts/`: MIT License.
- Original documentation and derived tabular outputs: CC BY 4.0.
- Third-party and upstream datasets retain their original provider licenses and terms.

## Citation

Until the Version 2 Zenodo record is published, cite the existing archived package as:

Adju, F.-N. A. (2026). *Jolo Island Surface Heat GeoAI: Reproducibility Package* (Version 1.0.0) [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.22541245

After Version 2 publication, `CITATION.cff` and this section will be updated with the new version-specific DOI.
