from pathlib import Path
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[2]
RASTER = ROOT / "data" / "rasters"
BOUND = ROOT / "data" / "boundaries"
OUT = ROOT / "data" / "derived"
OUT.mkdir(parents=True, exist_ok=True)

pred_path = RASTER / "Jolo_Predictor_Stack_v02.tif"
lst_path = RASTER / "Jolo_MAM_2013_2026_Median_LST_C.tif"
qc_path = RASTER / "Jolo_MAM_2013_2026_LST_QC.tif"
aoi_path = BOUND / "Jolo_Island_AOI.geojson"
muni_path = BOUND / "Jolo_Municipalities_Clipped.geojson"

with rasterio.open(pred_path) as ds:
    transform, crs, H, W = ds.transform, ds.crs, ds.height, ds.width
    descriptions = list(ds.descriptions)
    P = ds.read().astype("float32")

aoi = gpd.read_file(aoi_path).to_crs(crs)
mask = rasterize(
    [(geom, 1) for geom in aoi.geometry],
    out_shape=(H, W), transform=transform, fill=0, dtype="uint8"
)
coast_dist = distance_transform_edt(
    mask == 1, sampling=(abs(transform.e), transform.a)
).astype("float32")
coast_dist[mask == 0] = np.nan

def align(src_path, band, resampling):
    with rasterio.open(src_path) as src:
        source = src.read(band).astype("float32")
        dst = np.full((H, W), np.nan, dtype="float32")
        reproject(
            source=source, destination=dst,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=transform, dst_crs=crs,
            resampling=resampling, src_nodata=np.nan, dst_nodata=np.nan
        )
        return dst

lst = align(lst_path, 1, Resampling.bilinear)
obs = align(qc_path, 1, Resampling.nearest)
lstsd = align(qc_path, 2, Resampling.bilinear)
stqa = align(qc_path, 3, Resampling.bilinear)

bands = {d: P[i] for i, d in enumerate(descriptions)}
bands["distance_to_coast_m"] = coast_dist
bands["GHSL_built_local_fraction"] = bands["GHSL_built_surface_m2"] / 100.0

rows, cols = np.indices((H, W))
xs = transform.c + (cols + 0.5) * transform.a
ys = transform.f + (rows + 0.5) * transform.e

lattice = (rows % 10 == 5) & (cols % 10 == 5)
wc = bands["WorldCover_2021"]
domain = (
    (mask == 1) & np.isfinite(lst) & np.isfinite(obs) &
    (obs >= 10) & np.isfinite(wc) & (wc != 80)
)
sel = domain & lattice

df = pd.DataFrame({
    "LST_MAM_median_C": lst[sel],
    "valid_obs": obs[sel],
    "LST_MAM_SD_C": lstsd[sel],
    "ST_QA_median_K": stqa[sel],
    "NDVI_MAM_median": bands["NDVI_MAM_median"][sel],
    "NDBI_MAM_median": bands["NDBI_MAM_median"][sel],
    "NDMI_MAM_median": bands["NDMI_MAM_median"][sel],
    "BSI_MAM_median": bands["BSI_MAM_median"][sel],
    "GHSL_built_local_fraction": bands["GHSL_built_local_fraction"][sel],
    "WorldCover_2021": wc[sel],
    "elevation_m": bands["elevation_m"][sel],
    "slope_deg": bands["slope_deg"][sel],
    "northness": bands["northness"][sel],
    "eastness": bands["eastness"][sel],
    "distance_to_coast_m": coast_dist[sel],
    "distance_to_permanent_water_m": bands["distance_to_inland_water_m"][sel],
    "x_utm": xs[sel],
    "y_utm": ys[sel],
    "row": rows[sel],
    "col": cols[sel],
}).replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)

pts_ll = gpd.GeoSeries(gpd.points_from_xy(df.x_utm, df.y_utm), crs=crs).to_crs(4326)
df["longitude"] = pts_ll.x.to_numpy()
df["latitude"] = pts_ll.y.to_numpy()

for km in [1, 2, 3, 5]:
    s = km * 1000
    df[f"block{km}km_x"] = np.floor(df.x_utm / s).astype(int)
    df[f"block{km}km_y"] = np.floor(df.y_utm / s).astype(int)
    df[f"block{km}km_id"] = (
        df[f"block{km}km_x"].astype(str) + "_" + df[f"block{km}km_y"].astype(str)
    )

muni = gpd.read_file(muni_path).to_crs(crs)
name_col = "shapeName" if "shapeName" in muni.columns else [c for c in muni.columns if "name" in c.lower()][0]
points = gpd.GeoDataFrame(
    df.copy(), geometry=gpd.points_from_xy(df.x_utm, df.y_utm), crs=crs
)
joined = gpd.sjoin(points, muni[[name_col, "geometry"]], how="left", predicate="within")
df["municipality"] = joined[name_col].to_numpy()

out = OUT / "Jolo_Modeling_Sample_Rebuilt.csv"
df.to_csv(out, index=False)
print(f"Wrote {len(df):,} rows to {out}")
