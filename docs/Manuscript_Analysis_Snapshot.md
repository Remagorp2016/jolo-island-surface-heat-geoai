# Explaining Fine-Scale Surface Heat Across a Tropical Volcanic Island Using Spatially Validated GeoAI: Jolo Island, Philippines

## Abstract
Land-surface temperature (LST) studies increasingly use machine learning and explainable artificial intelligence, but model evaluation often relies on random data partitions that can overstate spatial generalization. This study develops a spatially validated, explainable GeoAI framework for mapping and attributing surface heat across Jolo Island, Philippines, a tropical volcanic island with strong gradients in elevation, vegetation, coastal proximity, and settlement intensity. Landsat 8/9 Collection 2 Level-2 observations from March–May 2013–2026 were quality masked and aggregated to a multi-year median daytime LST surface. Pixels with fewer than 10 valid thermal observations were excluded, retaining approximately 95.6% of the island. A 300-m systematic lattice yielded 8,838 terrestrial modeling samples. Candidate predictors represented vegetation, built/bare surface conditions, land cover, elevation, slope, terrain orientation, and distance to coast. Redundancy screening removed exact or near-exact spectral and distance-variable duplicates before modeling. LightGBM, XGBoost, random forest, and linear regression were compared under random and spatially blocked cross-validation. LightGBM achieved R²=0.729 under random five-fold cross-validation, decreasing only modestly to R²=0.706 under 3-km blocked cross-validation and R²=0.686 under 5-km blocking. Leave-one-municipality-out evaluation yielded R²=0.669. SHAP analysis identified elevation and vegetation as the strongest cooling controls, followed by NDBI, coastal distance, and eastness. Seasonal sensitivity analyses using independently constructed JJA and DJF climatologies preserved the same dominant terrain–vegetation–built-surface structure: elevation ranked first by SHAP in all seasons, while 3-km blocked LightGBM R² remained 0.715 for the MAM sensitivity rerun, 0.646 for JJA, and 0.669 for DJF. Residuals nevertheless retained significant local spatial autocorrelation (Moran’s I≈0.53, permutation p=0.005), indicating unresolved spatial processes. The results demonstrate that spatial validation materially strengthens interpretation of satellite-derived surface-heat models and provide a reproducible framework for heat attribution in data-sparse tropical islands.

**Keywords:** land surface temperature; GeoAI; explainable machine learning; SHAP; spatial cross-validation; Landsat; tropical island; Jolo; Philippines

## 1. Introduction
Satellite-derived LST provides spatially continuous information on the thermal state of the land surface and has become central to studies of urban heat, environmental exposure, and land–atmosphere interactions. Recent work increasingly combines remotely sensed LST with machine-learning models and SHAP-based interpretation. Reviews published in 2025–2026 show a broader shift from purely predictive urban thermal modeling toward interpretable and decision-oriented machine learning. However, spatial autocorrelation remains a major methodological challenge: geographically nearby training and validation pixels can share environmental structure, producing optimistic performance estimates when conventional random cross-validation is used.

The methodological problem is particularly relevant for fine-resolution island studies. Small tropical islands combine strong coastal influence, steep terrain, heterogeneous vegetation, localized settlement, and limited meteorological monitoring. Their environmental gradients occur over short distances, making spatial leakage especially plausible. At the same time, such islands are underrepresented in the rapidly expanding GeoAI and urban-thermal literature.

Jolo Island in the southern Philippines offers a useful test case. Rather than treating heat exclusively as an urban-versus-rural contrast, this study models surface heat continuously across the entire physical island. Jolo Municipality therefore represents one end of a broader island thermal gradient that also includes forested uplands, agricultural landscapes, coastal settlements, mangrove areas, and other municipalities.

### 1.1 Research gap
Three gaps motivate the study. First, LST–ML–SHAP studies are now common, so explainability alone is insufficient methodological novelty. Second, many geospatial ML studies still depend heavily on random validation despite known spatial dependence. Third, tropical small-island heat studies with island-wide, multi-year Earth-observation data and explicit geographic-transfer tests remain uncommon.

### 1.2 Objectives
This study aims to: (1) derive a robust multi-year MAM median LST surface for Jolo Island; (2) quantify associations between surface heat and vegetation, built/bare-surface, terrain, land-cover, and coastal predictors; (3) compare statistical and machine-learning models under random, spatially blocked, and municipality-held-out validation; (4) explain the best-performing model using SHAP; (5) diagnose residual spatial autocorrelation; and (6) map relative thermal regimes across the island.

## 2. Materials and Methods

### 2.1 Study area and boundary construction
The analytical domain is the physical Jolo mainland rather than an administrative municipality. Municipality-level geoBoundaries ADM3 polygons for the 11 municipalities intersecting Jolo Island were dissolved, decomposed into disconnected polygon components, and the largest connected component was retained as the physical island domain. This removed offshore islands while preserving the complete Jolo mainland, including Omar. The resulting geometry was topologically valid and approximately 835–838 km² depending on geodesic/raster calculation method.

### 2.2 Landsat thermal archive audit
Landsat 8 and Landsat 9 Collection 2 Tier 1 Level-2 scenes intersecting Jolo Island were audited from 18 March 2013 through 6 September 2026. Only L2SP products containing the surface-temperature product were retained. The archive contained 715 candidate thermal scenes (527 Landsat 8 and 188 Landsat 9). Metadata screening found 103 scenes with CLOUD_COVER≤10%, 202≤20%, and 299≤30%.

### 2.3 Temporal design and LST derivation
Observation-density analysis compared MAM, JJA, DJF, and all-year windows. MAM provided the strongest seasonal observation density, with a mean of 41.6 valid observations per pixel, median 38, and fifth percentile approximately 21.5 observations. The primary response was therefore defined as the March–May 2013–2026 median daytime LST.

For each Landsat image, QA_PIXEL bits for fill, dilated cloud, cirrus, cloud, cloud shadow, and snow were masked, and radiometrically saturated pixels were removed using QA_RADSAT. Collection 2 Level-2 ST_B10 values were converted to degrees Celsius as:

LST (°C) = ST_B10 × 0.00341802 + 149.0 − 273.15.

Values outside a broad 10–60°C physical sanity range were excluded. Pixels required at least 10 valid MAM observations. This retained about 801.5 km², equivalent to approximately 95.6% of the AOI. The resulting LST surface had mean 32.04°C, median 32.00°C, P5 28.34°C, and P95 35.63°C.

### 2.4 Predictor variables
Candidate environmental predictors represented multiple physical mechanisms: NDVI (vegetation), NDBI (built/bare spectral response), NDMI, BSI, GHSL built surface, ESA WorldCover class, elevation, slope, northness, eastness, distance to coastline, and distance to permanent water. MAM Landsat spectral indices were composited across the same 2013–2026 seasonal window as the LST response. NASADEM supplied elevation and terrain derivatives, while structural built-up and land-cover layers were obtained from GHSL and ESA WorldCover.

A corrected Euclidean distance-to-coast surface was derived in UTM Zone 51N from the final island polygon rather than relying on the initially exported erroneous distance band. Maximum interior distance was approximately 9.8 km. GHSL built-up surface was independently checked at the 30-m scale. Because Earth Engine `reduceResolution()` uses fractional overlap weights, the validation layer was converted to built fraction using the overlap-weighted 10-m built-surface value divided by 100 m². This independently derived 30-m fraction closely agreed with the locally constructed built fraction used in the primary model (Pearson r=0.914; mean fractions 0.0070 and 0.0071).

### 2.5 Redundancy and feature selection
A 300-m systematic sample produced 8,838 valid terrestrial observations. Pairwise correlations and VIF were used as a pre-model audit. NDBI and NDMI were exact inverses (Pearson r=−1.000), and BSI was strongly correlated with NDBI (r=0.988) and NDVI (r=−0.873). Distance to permanent water was also highly correlated with distance to coast (r=0.952). To stabilize interpretation, NDMI, BSI, and distance-to-permanent-water were excluded from the final explanatory feature set. The retained continuous predictors were NDVI, NDBI, GHSL built-surface proxy, elevation, slope, northness, eastness, and distance to coast. WorldCover was treated categorically rather than as a continuous numerical code. After screening, VIF values of the core continuous predictors were all below approximately 4.

### 2.6 Sampling and spatial partitioning
The final modeling sample used one native 30-m observation every 10 pixels in each x/y direction, corresponding to approximately 300-m systematic spacing. The sample covered all 11 Jolo Island municipalities and 915 1-km blocks, 255 2-km blocks, 126 3-km blocks, and 54 5-km blocks.

Longitude and latitude were retained only for diagnostics and visualization, not as ordinary predictive covariates, to reduce the risk that models learned location directly rather than environmental controls.

### 2.7 Statistical and machine-learning models
Linear regression served as the statistical baseline. Random forest, XGBoost, and LightGBM represented nonlinear ensemble learners. WorldCover was one-hot encoded and rare classes were pooled. Continuous predictors were standardized for the linear model and preprocessing consistency.

### 2.8 Validation strategy
Performance was evaluated with R², RMSE, and MAE. Three validation regimes were used: (1) random five-fold cross-validation; (2) blocked five-fold cross-validation using 1-, 2-, 3-, and 5-km spatial blocks; and (3) leave-one-municipality-out testing. The primary spatial-performance interpretation emphasizes the 3-km blocked scheme, while multiple block sizes quantify sensitivity to spatial separation.

### 2.9 Explainable AI
The best spatially validated model was refitted to the full modeling sample and interpreted using TreeSHAP. Global importance was summarized using mean absolute SHAP values. For continuous predictors, Spearman correlations between predictor values and their SHAP contributions were calculated as a compact diagnostic of dominant effect direction.

### 2.10 Residual spatial diagnostics
Out-of-fold residuals from 3-km blocked LightGBM predictions were evaluated using a row-standardized 8-nearest-neighbor Moran’s I statistic. Significance was assessed with 199 random permutations.

### 2.11 Thermal-regime mapping
Relative thermal regimes were defined from the modeling-sample LST distribution: cool ≤P20 (30.27°C), hot ≥P80 (33.83°C), very hot ≥P90 (34.76°C), and extreme hot ≥P95 (35.67°C). A raster regime map was produced on the 30-m UTM analysis grid.

### 2.12 Seasonal robustness and GHSL aggregation audit
To test whether the primary MAM interpretation depended on seasonal choice, independent JJA (June–August) and DJF (December–February) median LST, NDVI, NDBI, and BSI surfaces were constructed from the same 2013–2026 Landsat archive and QA rules. Seasonal models used the same 300-m sample locations, static terrain, coastline distance, categorical WorldCover treatment, and LightGBM configuration as the primary analysis. Models were evaluated under random five-fold CV, 1-, 2-, 3-, and 5-km blocked CV, and leave-one-municipality-out testing. A ≥20-valid-observation sensitivity analysis was also performed.

The GHSL 10-m `built_surface` product is expressed as square metres of built surface per 10-m cell. Earth Engine `reduceResolution()` weights input pixels by fractional overlap with the output pixel; therefore a naive weighted sum divided by the 30-m cell area underestimates built fraction. The exported validation layer was corrected locally by converting the overlap-weighted built-surface value to fraction relative to the native 100-m² cell area. The corrected 30-m result was compared against the independently constructed local built-fraction predictor used in the primary model.

## 3. Results

### 3.1 LST climatology and thermal-regime area
The valid MAM LST surface covered approximately 95.6% of Jolo Island. Mean and median LST were approximately 32.04°C and 32.00°C, respectively. On the 30-m analysis grid, approximately 157.6 km² (19.8% of valid land) was classified cool, 481.0 km² (60.4%) moderate, 77.6 km² (9.7%) hot, 41.6 km² (5.2%) very hot, and 38.3 km² (4.8%) extreme hot.

### 3.2 Random versus spatial validation
LightGBM performed best under conventional random five-fold cross-validation (R²=0.729, RMSE=1.185°C, MAE=0.907°C), closely followed by XGBoost and random forest. The linear baseline reached R²=0.692.

Spatial blocking reduced performance as expected, but the decline was modest rather than catastrophic. LightGBM achieved R² values of 0.719, 0.708, 0.706, and 0.686 using 1-, 2-, 3-, and 5-km blocks, respectively. At 3 km, LightGBM produced RMSE=1.235°C and MAE=0.951°C. This represents an R² decline of about 0.023 relative to random CV, suggesting that conventional validation was somewhat optimistic but that most model skill transferred geographically.

### 3.3 Municipality-held-out generalization
Leave-one-municipality-out LightGBM evaluation across 11 municipalities yielded overall R²=0.669, RMSE=1.310°C, and MAE=1.018°C. Performance varied markedly among municipalities. Talipao and Patikul showed stronger held-out performance, while Jolo Municipality had poor municipality-specific R² because the 300-m lattice produced only 31 Jolo samples and the municipality occupies a distinct, very warm thermal regime. The Jolo-specific result should therefore be treated as a high-variance local diagnostic rather than a stable municipality-level performance estimate.

### 3.4 Dominant heat controls from SHAP
SHAP identified elevation as the dominant predictor (mean |SHAP|≈0.823°C), followed by NDVI (0.613°C), NDBI (0.305°C), distance to coast (0.251°C), and eastness (0.175°C). WorldCover, slope, northness, and the local GHSL built-surface proxy had smaller global contributions.

The direction diagnostics were physically coherent for the major variables. Higher elevation was strongly associated with cooling (Spearman correlation between feature value and SHAP contribution ≈−0.953), as was higher NDVI (≈−0.966). Higher NDBI was associated with warming (≈+0.959). Greater distance from the coast was associated with lower modeled LST (≈−0.757), implying that the hottest surfaces were preferentially concentrated in lower-elevation coastal/settled environments after accounting for the other predictors. Eastness showed a positive SHAP relationship (≈+0.933), consistent with stronger morning solar exposure of east-facing terrain during Landsat daytime overpass conditions; this interpretation should be presented as mechanistic plausibility rather than causal proof.

### 3.5 Linear-model comparison
Standardized linear coefficients supported several SHAP findings. Elevation showed the largest negative standardized coefficient (−1.053), NDBI the largest positive coefficient (+0.872), and distance to coast was negative (−0.238). Eastness was positive (+0.218). NDVI retained a negative coefficient (−0.198) after accounting for correlated spectral and terrain conditions. The built-surface proxy had a small positive coefficient (+0.108).

### 3.6 Residual spatial autocorrelation
Despite reasonable geographically transferred predictive skill, 3-km blocked-CV residuals remained strongly spatially autocorrelated (Moran’s I≈0.530; permutation p=0.005). This indicates that the predictor set does not fully represent all spatially structured heat controls. Likely missing processes include finer-scale built morphology, road/pavement patterns, local terrain configuration, and potentially climatological or surface-property variables not represented in the current stack. This residual structure should be treated as a substantive result rather than concealed through coordinate predictors.

### 3.7 Municipality thermal regimes
The sample-based thermal-regime analysis showed a pronounced concentration of extreme-hot samples in Jolo Municipality, although the 300-m sampling lattice yielded only 31 samples there. Omar, Patikul, Kalingalan Caluang, Parang, Old Panamao, Luuk, and Panglima Estino also contained nontrivial extreme-hot fractions. Municipality summaries are descriptive rather than exposure or health-risk measures.

### 3.8 Sensitivity checks
Applying a stricter ≥20-observation threshold retained 8,627 of the 8,838 systematic samples and changed median LST only slightly (32.01°C to 32.07°C). A ≥30 threshold retained 6,531 samples but shifted the median upward to approximately 32.62°C, indicating that very strict observation-count filtering preferentially removes parts of the cooler/spatially less-observed domain. Filtering median ST_QA uncertainty to ≤5.0, ≤5.5, or ≤6.0 K produced small shifts in median LST, supporting the stability of the primary climatology against reasonable uncertainty thresholds.

### 3.9 Seasonal robustness
Independent seasonal reruns confirmed that the principal explanatory structure was not unique to MAM. With a ≥10 valid-observation threshold, LightGBM random-CV R² was 0.746 for the MAM sensitivity reconstruction, 0.684 for JJA, and 0.709 for DJF. Under the primary 3-km blocked scheme, corresponding R² values were 0.715, 0.646, and 0.669, with RMSE values of 1.230°C, 1.145°C, and 1.077°C, respectively. Spatial skill declined smoothly with larger blocks; at 5 km, R² remained 0.705 for MAM, 0.638 for JJA, and 0.668 for DJF.

The seasonal thermal surfaces were themselves strongly related. At matched valid samples, MAM and JJA LST correlated at r=0.789, MAM and DJF at r=0.868, and JJA and DJF at r=0.749. MAM was approximately 0.26°C warmer than JJA and 0.90°C warmer than DJF on average.

SHAP rankings were also stable. Elevation ranked first in all three seasons. NDVI remained a cooling predictor, NDBI a warming predictor, greater distance to coast was associated with lower modeled LST, and eastness retained a positive effect direction. Rank correlations among the eight core continuous predictors were 0.905 for MAM–JJA, 0.857 for MAM–DJF, and 0.833 for JJA–DJF. The principal seasonal difference was a reduced relative importance of NDVI during JJA.

Applying a ≥20 seasonal observation threshold preserved the same broad findings, with 3-km blocked R² values of 0.708 for MAM, 0.604 for JJA, and 0.620 for DJF.

### 3.10 GHSL 30-m built-fraction validation
The independently checked 30-m GHSL fraction showed strong agreement with the locally constructed built-fraction predictor used in the primary analysis (Pearson r=0.914; Spearman ρ=0.803). Mean built fractions were 0.0070 and 0.0071, respectively. Replacing the local built fraction with the corrected GHSL30 validation layer changed primary MAM performance negligibly on the original modeling sample: random-CV R² changed from 0.730 to 0.729 and 3-km spatial-CV R² from 0.703 to 0.702. Built-surface implementation therefore had no material effect on the study conclusions.

## 4. Discussion

### 4.1 A terrain–vegetation–built-surface explanation of island heat
The dominant explanatory pattern is not simply an urban-versus-rural contrast. Elevation and vegetation exerted the strongest cooling contributions across the island, while higher NDBI and local built-surface signals were associated with warming. This supports an interpretation in which Jolo’s surface thermal field emerges from a coupled topographic and land-cover gradient: cooler vegetated uplands contrast with lower, more developed or exposed coastal environments.

### 4.2 Why spatial validation matters
Random CV produced the most optimistic metrics, but its advantage over blocked validation was modest. The relatively small decline from random R²=0.729 to 3-km blocked R²=0.706 is important because it suggests that the model is not merely memorizing neighboring pixels. The further decrease at 5-km blocking and municipality-held-out testing demonstrates, however, that transfer performance depends on spatial separation and environmental distinctness.

### 4.3 Interpreting coastal distance
Distance to coast showed a negative SHAP relationship: farther-inland locations tended to be cooler. The variable should not be interpreted as evidence that proximity to seawater intrinsically warms land surfaces. On Jolo, distance to coast is entangled with elevation, settlement geography, vegetation, and terrain. Its contribution is therefore best interpreted as a composite spatial-environmental gradient after adjustment for the included predictors.

### 4.4 Residual structure as evidence of missing mechanisms
The substantial residual Moran’s I reveals that environmental attribution is incomplete even when predictive accuracy appears satisfactory. Adding latitude/longitude could likely improve interpolation while obscuring the physical explanation. This study therefore deliberately leaves coordinates outside the explanatory model and reports residual autocorrelation transparently. Future work should test physically meaningful neighborhood variables, street/road density, built-form morphology, albedo, terrain-position indices, or meteorological covariates.

### 4.5 Implications for tropical small-island GeoAI
The workflow demonstrates that a data-sparse island can support a rigorous thermal-environment study without field respondents or dense weather-station networks. The key is not simply using ML, but combining a long EO archive, observation-density QC, redundancy screening, spatially explicit validation, explainability, and residual diagnostics.

### 4.6 Seasonal persistence of the island thermal structure
The seasonal sensitivity analysis strengthens the interpretation of a persistent island thermal geography. Absolute model skill varied among MAM, JJA, and DJF, but elevation remained the dominant explanatory feature and the directions of vegetation, built/exposed surface, coastal distance, and eastness effects were preserved. This consistency argues against interpreting the primary MAM findings as an artifact of one seasonal window. The lower relative NDVI importance in JJA is also physically plausible in a wetter, more uniformly vegetated seasonal state, where vegetation contrast across the island is reduced and topographic control becomes relatively more dominant.

## 5. Limitations
1. The response is satellite land-surface temperature, not near-surface air temperature or human thermal exposure.
2. The seasonal medians represent clear-sky daytime surface conditions and do not describe nighttime heat.
3. Spectral indices and LST are derived from the same seasonal Landsat archive; associations are explanatory/predictive, not causal effects.
4. GHSL and WorldCover are structural reference layers from specific years within or near the climatological period, although an independent 30-m GHSL aggregation audit showed that built-fraction implementation had negligible influence on model performance.
5. Significant spatial autocorrelation remains in blocked-CV residuals.
6. Municipality-level comparisons, especially Jolo Municipality, are sensitive to the 300-m systematic sampling density.
7. Seasonal robustness was assessed for MAM, JJA, and DJF, but the study does not model individual weather events, interannual extremes, nighttime thermal conditions, or monsoon-transition dynamics.

## 6. Conclusion
A spatially validated explainable GeoAI framework successfully modeled the fine-scale MAM surface-temperature gradient across Jolo Island. LightGBM retained substantial predictive skill under 3-km spatial blocking and municipality-held-out testing, while SHAP consistently identified elevation and vegetation as dominant cooling controls and built/bare spectral response as a major warming control. The modest random-to-spatial validation gap indicates genuine geographic transferability, but strong residual spatial autocorrelation shows that predictive accuracy does not imply complete environmental explanation. Seasonal sensitivity analysis further showed that elevation remained the leading driver across MAM, JJA, and DJF and that vegetation, built/exposed surface response, coastal position, and terrain orientation retained consistent effect directions. The study therefore supports a broader methodological conclusion: geospatial heat modeling should combine explainability, seasonal robustness, spatial validation, and residual diagnostics rather than treating high random-CV accuracy as sufficient evidence of robust spatial understanding.

## Provisional literature anchors
- Recent systematic review of ML in urban thermal environments: Sustainable Cities and Society (2026), doi:10.1016/j.scs.2026.107400.
- Recent review of ML for urban heat-island applications: Sustainable Cities and Society (2025), doi:10.1016/j.scs.2025.106943.
- Spatial predictor selection and geolocation-overfitting discussion: Ecological Modelling (2019), doi:10.1016/j.ecolmodel.2019.108815.
- Spatially aware tuning/evaluation: Ecological Modelling (2019), doi:10.1016/j.ecolmodel.2019.06.002.
- Remote-sensing validation inflation under spatial autocorrelation: ISPRS Open Journal of Photogrammetry and Remote Sensing (2022), doi:10.1016/j.ophoto.2022.100018.
- Spatial+ geospatial cross-validation: International Journal of Applied Earth Observation and Geoinformation (2023), doi:10.1016/j.jag.2023.103364.

