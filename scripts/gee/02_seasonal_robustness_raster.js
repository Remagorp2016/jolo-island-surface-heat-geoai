// Jolo Island Surface Heat GeoAI
// Seasonal robustness raster (MAM/JJA/DJF + GHSL 30 m built fraction)
// Earth Engine JavaScript

var aoiFC = ee.FeatureCollection(
  'projects/sulu-flood-research/assets/Jolo_Island_AOI'
);

var workRegion = ee.Geometry.Rectangle(
  [120.90, 5.78, 121.46, 6.17], null, false
);

var analysisCRS = 'EPSG:32651';
var analysisScale = 30;

var islandMask = ee.Image(0).byte().paint({
  featureCollection: aoiFC,
  color: 1
}).clip(workRegion).reproject({
  crs: analysisCRS,
  scale: analysisScale
}).rename('island');

var l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
  .filterBounds(workRegion)
  .filterDate('2013-03-18', '2026-09-07')
  .filter(ee.Filter.eq('PROCESSING_LEVEL', 'L2SP'));

var l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
  .filterBounds(workRegion)
  .filterDate('2013-03-18', '2026-09-07')
  .filter(ee.Filter.eq('PROCESSING_LEVEL', 'L2SP'));

var landsat = l8.merge(l9);
var mam = landsat.filter(ee.Filter.calendarRange(3, 5, 'month'));
var jja = landsat.filter(ee.Filter.calendarRange(6, 8, 'month'));
var djf = landsat.filter(ee.Filter.or(
  ee.Filter.calendarRange(12, 12, 'month'),
  ee.Filter.calendarRange(1, 2, 'month')
));

function prepareIndices(image) {
  var qa = image.select('QA_PIXEL');
  var clear = qa.bitwiseAnd(1 << 0).eq(0)
    .and(qa.bitwiseAnd(1 << 1).eq(0))
    .and(qa.bitwiseAnd(1 << 2).eq(0))
    .and(qa.bitwiseAnd(1 << 3).eq(0))
    .and(qa.bitwiseAnd(1 << 4).eq(0))
    .and(qa.bitwiseAnd(1 << 5).eq(0));
  var unsaturated = image.select('QA_RADSAT').eq(0);

  var optical = image.select(['SR_B2','SR_B4','SR_B5','SR_B6'])
    .multiply(0.0000275).add(-0.2)
    .updateMask(clear.and(unsaturated));

  var blue = optical.select('SR_B2');
  var red = optical.select('SR_B4');
  var nir = optical.select('SR_B5');
  var swir1 = optical.select('SR_B6');

  var ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI');
  var ndbi = swir1.subtract(nir).divide(swir1.add(nir)).rename('NDBI');
  var bsi = swir1.add(red).subtract(nir.add(blue))
    .divide(swir1.add(red).add(nir.add(blue))).rename('BSI');

  return ee.Image.cat([ndvi, ndbi, bsi]);
}

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
    .multiply(0.00341802).add(149.0).subtract(273.15)
    .rename('LST_C');
  return lst.updateMask(clear.and(unsaturated).and(lst.gt(10)).and(lst.lt(60)));
}

function seasonBands(collection, prefix) {
  var spectral = collection.map(prepareIndices).median();
  var lstCollection = collection.map(prepareLST);
  return ee.Image.cat([
    lstCollection.median().rename(prefix + '_LST_C'),
    lstCollection.count().rename(prefix + '_valid_obs'),
    spectral.select('NDVI').rename(prefix + '_NDVI'),
    spectral.select('NDBI').rename(prefix + '_NDBI'),
    spectral.select('BSI').rename(prefix + '_BSI')
  ]);
}

var ghsl10 = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S_10m/2018')
  .select('built_surface').clip(workRegion);

// Correct fraction: per-10m-cell fraction first, then mean aggregation.
var builtFraction30 = ghsl10.divide(100)
  .reduceResolution({
    reducer: ee.Reducer.mean(),
    maxPixels: 16
  })
  .reproject({
    crs: analysisCRS,
    scale: analysisScale
  })
  .clamp(0, 1)
  .rename('GHSL_built_fraction_30m');

var worldCover = ee.ImageCollection('ESA/WorldCover/v200')
  .first().select('Map');
var terrestrial = islandMask.eq(1).and(worldCover.neq(80));

var stack = ee.Image.cat([
  seasonBands(mam, 'MAM'),
  seasonBands(jja, 'JJA'),
  seasonBands(djf, 'DJF'),
  builtFraction30
]).updateMask(terrestrial).clip(workRegion);

Export.image.toDrive({
  image: stack.toFloat(),
  description: 'Jolo_Seasonal_Robustness_Raster_v02',
  folder: 'Jolo_Heat_Research',
  fileNamePrefix: 'Jolo_Seasonal_Robustness_Raster_v02',
  region: workRegion,
  scale: 30,
  crs: analysisCRS,
  maxPixels: 1e9,
  fileFormat: 'GeoTIFF'
});
