// Jolo Island Surface Heat GeoAI
// Primary MAM LST response, Collection 2 Level-2
// Earth Engine JavaScript

var aoiFC = ee.FeatureCollection(
  'projects/sulu-flood-research/assets/Jolo_Island_AOI'
);
var aoi = aoiFC.geometry();

var l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
  .filterBounds(aoi)
  .filterDate('2013-03-18', '2026-09-07')
  .filter(ee.Filter.eq('PROCESSING_LEVEL', 'L2SP'));

var l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
  .filterBounds(aoi)
  .filterDate('2013-03-18', '2026-09-07')
  .filter(ee.Filter.eq('PROCESSING_LEVEL', 'L2SP'));

var mam = l8.merge(l9)
  .filter(ee.Filter.calendarRange(3, 5, 'month'));

function prepareLST(image) {
  var qa = image.select('QA_PIXEL');
  var clear = qa.bitwiseAnd(1 << 0).eq(0)
    .and(qa.bitwiseAnd(1 << 1).eq(0))
    .and(qa.bitwiseAnd(1 << 2).eq(0))
    .and(qa.bitwiseAnd(1 << 3).eq(0))
    .and(qa.bitwiseAnd(1 << 4).eq(0))
    .and(qa.bitwiseAnd(1 << 5).eq(0));

  var unsaturated = image.select('QA_RADSAT').eq(0);

  var lst = image.select('ST_B10')
    .multiply(0.00341802)
    .add(149.0)
    .subtract(273.15)
    .rename('LST_C');

  var uncertainty = image.select('ST_QA')
    .multiply(0.01)
    .rename('ST_uncertainty_K');

  var plausible = lst.gt(10).and(lst.lt(60));
  var valid = clear.and(unsaturated).and(lst.mask()).and(plausible);

  return lst.addBands(uncertainty)
    .updateMask(valid)
    .copyProperties(image, ['system:time_start']);
}

var prepared = mam.map(prepareLST);
var lstMedian = prepared.select('LST_C').median()
  .clip(aoi).rename('LST_MAM_median_C');
var obsCount = prepared.select('LST_C').count()
  .clip(aoi).rename('valid_obs');
var lstSD = prepared.select('LST_C').reduce(ee.Reducer.stdDev())
  .clip(aoi).rename('LST_MAM_SD_C');
var uncertaintyMedian = prepared.select('ST_uncertainty_K').median()
  .clip(aoi).rename('ST_QA_median_K');

var reliable = obsCount.gte(10);
var finalLST = lstMedian.updateMask(reliable);
var qcStack = obsCount.toFloat()
  .addBands(lstSD.updateMask(reliable).toFloat())
  .addBands(uncertaintyMedian.updateMask(reliable).toFloat());

var exportRegion = aoi.bounds(100);

Export.image.toDrive({
  image: finalLST.toFloat(),
  description: 'Jolo_MAM_2013_2026_Median_LST_C',
  folder: 'Jolo_Heat_Research',
  fileNamePrefix: 'Jolo_MAM_2013_2026_Median_LST_C',
  region: exportRegion,
  scale: 30,
  crs: 'EPSG:32651',
  maxPixels: 1e9,
  fileFormat: 'GeoTIFF'
});

Export.image.toDrive({
  image: qcStack,
  description: 'Jolo_MAM_2013_2026_LST_QC',
  folder: 'Jolo_Heat_Research',
  fileNamePrefix: 'Jolo_MAM_2013_2026_LST_QC',
  region: exportRegion,
  scale: 30,
  crs: 'EPSG:32651',
  maxPixels: 1e9,
  fileFormat: 'GeoTIFF'
});
