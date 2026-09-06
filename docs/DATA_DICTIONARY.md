# Data dictionary

## `Jolo_Modeling_Sample_Local_v03.csv`

| Variable | Meaning |
|---|---|
| LST_MAM_median_C | MAM 2013–2026 median LST, °C |
| valid_obs | Number of valid MAM thermal observations |
| LST_MAM_SD_C | Temporal SD of valid MAM LST observations, °C |
| ST_QA_median_K | Median Landsat ST uncertainty estimate, K |
| NDVI_MAM_median | MAM median NDVI |
| NDBI_MAM_median | MAM median normalized difference built-up index |
| NDMI_MAM_median | MAM median normalized difference moisture index |
| BSI_MAM_median | MAM median bare soil index |
| GHSL_built_local_fraction | Main-analysis GHSL local built fraction |
| WorldCover_2021 | ESA WorldCover categorical class code |
| elevation_m | NASADEM elevation, m |
| slope_deg | Terrain slope, degrees |
| northness | cos(aspect), range −1 to 1 |
| eastness | sin(aspect), range −1 to 1 |
| distance_to_coast_m | Distance to physical-island coastline, m |
| distance_to_permanent_water_m | Distance to permanent-water pixels, m |
| x_utm, y_utm | UTM Zone 51N coordinates, m |
| row, col | Source analysis-grid row/column |
| longitude, latitude | Geographic coordinates used for diagnostics only |
| block*km_* / block*km_id | Spatial CV block coordinates/IDs |
| municipality | Municipality assignment for geographic holdout validation |

## `Jolo_Seasonal_Robustness_ModelSample_v04.csv`

Contains the same static terrain/geographic framework plus season-specific MAM/JJA/DJF LST, valid-observation count, NDVI, NDBI, BSI, and the corrected 30 m GHSL built fraction.

`GHSL_built_fraction_30m_corrected` is the final independent 30 m built-fraction implementation used in the robustness analysis.
