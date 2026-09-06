# Jolo Island Surface Heat GeoAI

Reproducibility repository for:

**Explaining Fine-Scale Surface Heat Across a Tropical Volcanic Island Using Spatially Validated GeoAI: Jolo Island, Philippines**

**Author:** Fadzlur-Nijar A. Adju  
**Affiliation:** College of Computing Studies, Mindanao State University–Sulu, Philippines  
**ORCID:** https://orcid.org/0009-0003-1865-7596  
**Corresponding author:** fadzlur-nijar.adju@msusulu.edu.ph

## Study overview

This repository contains the derived datasets, analysis scripts, model outputs, and figures used to evaluate island-wide land surface temperature (LST) controls across Jolo Island, Philippines. The workflow combines Landsat 8/9 Collection 2 Level-2 surface temperature, spectral indices, GHSL built-up information, ESA WorldCover, NASADEM terrain variables, spatially blocked cross-validation, municipality-held-out validation, SHAP explainability, seasonal robustness tests, and residual spatial diagnostics.

The primary response is the **March–May (MAM) 2013–2026 median daytime Landsat LST climatology**. A 300 m systematic sampling lattice produced **8,838 terrestrial samples** for the main analysis.

Key reported results include:

- LightGBM random 5-fold CV: **R² ≈ 0.729**
- LightGBM 3 km spatial-block CV: **R² ≈ 0.706**
- LightGBM 5 km spatial-block CV: **R² ≈ 0.686**
- Leave-one-municipality-out overall: **R² ≈ 0.669**
- Residual Moran's I: **≈ 0.530** with permutation **p = 0.005**
- Elevation and NDVI are the leading cooling controls; NDBI is a major warming control
- The broad driver hierarchy persists across MAM, JJA, and DJF climatologies

## Repository structure

```text
.
├── CITATION.cff
├── LICENSE
├── README.md
├── requirements.txt
├── environment.yml
├── data/
│   ├── boundaries/
│   └── derived/
├── docs/
├── figures/
├── metadata/
├── results/
│   ├── core/
│   └── seasonal/
└── scripts/
    ├── gee/
    └── python/
```

## Reproducibility levels

### Level 1 — Reproduce the reported statistical/ML results

The files in `data/derived/` are analysis-ready and are sufficient to rerun the core and seasonal model evaluations without downloading raw Earth-observation archives.

Run:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python scripts/python/run_reproduction.py
```

Outputs are written to `reproduced_results/`.

### Level 2 — Reconstruct the main sample from exported rasters

The full Zenodo archive includes the larger intermediate GeoTIFFs used to reconstruct the main analysis sample. See `scripts/python/build_main_sample_from_rasters.py`.

### Level 3 — Upstream Earth Engine processing

Representative final Google Earth Engine scripts are included in `scripts/gee/`. Raw Landsat, GHSL, ESA WorldCover, NASADEM, and other provider archives are **not redistributed**. They remain available from their respective providers.

## Data notes

`Jolo_Modeling_Sample_Local_v03.csv` is the frozen main 300 m modeling sample.

`Jolo_Seasonal_Robustness_ModelSample_v04.csv` is the frozen seasonal robustness sample containing MAM, JJA, and DJF response/predictor values and the corrected 30 m GHSL built fraction.

Coordinates are provided for reproducibility and spatial partitioning. Longitude/latitude were **not** used as ordinary explanatory predictors in the reported models.

WorldCover class is categorical and is one-hot encoded during modeling. Rare classes with fewer than 30 observations are collapsed to `Other`.

## Software environment

The final analysis was run with Python 3.11 and the package versions recorded in `requirements.txt`.

All random operations use fixed seeds as recorded in the scripts.

## Data availability and DOI

A versioned full reproducibility archive is intended for deposit in Zenodo. After publication of the Zenodo record, replace this line with the assigned DOI:

**Zenodo DOI: TO BE ASSIGNED**

The GitHub repository and Zenodo record should be cross-linked as related research outputs.

## Authorship and declarations

**Sole author:** Fadzlur-Nijar A. Adju

**Funding:** This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

**Competing interests:** The author declares no conflict of interest.

**Acknowledgments:** None.

**Ethics:** Not applicable. The study uses satellite, gridded geospatial, and administrative-boundary data and involves no human participants, personal data, or animals.

See `metadata/DECLARATIONS.md` for the full statements.

## Licenses

- Analysis code in `scripts/`: MIT License.
- Original documentation and derived tabular outputs in this repository: CC BY 4.0.
- Third-party and upstream datasets retain their original provider licenses and terms. No claim of ownership is made over source products.

## Citation

Until the article and Zenodo DOI are available, cite the repository using `CITATION.cff`. After Zenodo publication, update the citation with the version DOI.
