# Data sources and provenance

The study uses publicly accessible Earth-observation and geospatial products.

| Source | Role |
|---|---|
| Landsat 8/9 Collection 2 Tier 1 Level-2 | Surface temperature and surface reflectance |
| ESA WorldCover 2021 v200 | Land-cover class |
| GHSL GHS-BUILT-S R2023A | Built-up surface/built fraction |
| NASADEM HGT v001 | Elevation and terrain derivatives |
| geoBoundaries ADM3 | Municipality framework |
| Final Jolo physical-island AOI | Derived study boundary |

## Important redistribution note

Raw provider archives are not included in this repository. The included tables and rasters are derived research products. Source datasets retain their original provider licenses, citations, and terms.

## Landsat thermal scaling

Collection 2 Level-2 `ST_B10` was converted to degrees Celsius as:

`LST_C = ST_B10 * 0.00341802 + 149.0 - 273.15`

Quality masking excluded fill, dilated cloud, cirrus, cloud, cloud shadow, snow, radiometrically saturated pixels, and implausible LST outside the broad 10–60 °C sanity range.

## Primary temporal design

The primary response is the March–May median LST climatology over the 2013–2026 Landsat archive. Seasonal robustness analyses repeat the design for JJA and DJF.

## Spatial sampling

The main frozen sample uses a systematic 300 m lattice over terrestrial Jolo Island pixels satisfying the thermal-observation threshold.
