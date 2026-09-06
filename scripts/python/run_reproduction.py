from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import KFold, GroupKFold, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import NearestNeighbors
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
import statsmodels.api as sm
import shap

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "derived"
OUT = ROOT / "reproduced_results"
OUT.mkdir(exist_ok=True)

def metrics(y_true, y_pred):
    return {
        "R2": r2_score(y_true, y_pred),
        "RMSE": mean_squared_error(y_true, y_pred) ** 0.5,
        "MAE": mean_absolute_error(y_true, y_pred),
    }

# ------------------------------------------------------------------
# Main MAM sample
# ------------------------------------------------------------------
df = pd.read_csv(DATA / "Jolo_Modeling_Sample_Local_v03.csv")
wc = df["WorldCover_2021"].astype(int).astype(str)
vc = wc.value_counts()
df["WorldCover_cat"] = wc.where(~wc.isin(vc[vc < 30].index), "Other")

num = [
    "NDVI_MAM_median",
    "NDBI_MAM_median",
    "GHSL_built_local_fraction",
    "elevation_m",
    "slope_deg",
    "northness",
    "eastness",
    "distance_to_coast_m",
]
cat = ["WorldCover_cat"]
X = df[num + cat]
y = df["LST_MAM_median_C"].to_numpy()

pre = ColumnTransformer([
    ("num", StandardScaler(), num),
    ("wc", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat),
])

models = {
    "Linear": LinearRegression(),
    "RandomForest": RandomForestRegressor(
        n_estimators=250, min_samples_leaf=2, max_features=0.8,
        n_jobs=-1, random_state=42
    ),
    "XGBoost": XGBRegressor(
        n_estimators=250, max_depth=6, learning_rate=0.05,
        subsample=0.85, colsample_bytree=0.85, reg_lambda=1.0,
        objective="reg:squarederror", n_jobs=-1, random_state=42
    ),
    "LightGBM": LGBMRegressor(
        n_estimators=250, num_leaves=31, learning_rate=0.05,
        subsample=0.85, colsample_bytree=0.85, reg_lambda=1.0,
        random_state=42, verbosity=-1, n_jobs=-1
    ),
}

# Random CV
kf = KFold(5, shuffle=True, random_state=42)
rows = []
for name, model in models.items():
    pred = cross_val_predict(
        Pipeline([("pre", pre), ("model", model)]),
        X, y, cv=kf, n_jobs=1
    )
    rows.append({"Model": name, **metrics(y, pred)})
pd.DataFrame(rows).to_csv(OUT / "RandomCV.csv", index=False)

# Spatial block CV
spatial = []
pred3 = {}
for km in [1, 2, 3, 5]:
    groups = df[f"block{km}km_id"].to_numpy()
    cv = GroupKFold(5)
    for name, model in models.items():
        pred = cross_val_predict(
            Pipeline([("pre", pre), ("model", model)]),
            X, y, cv=cv.split(X, y, groups), n_jobs=1
        )
        spatial.append({
            "Block_km": km,
            "Model": name,
            "n_groups": len(np.unique(groups)),
            **metrics(y, pred)
        })
        if km == 3:
            pred3[name] = pred
pd.DataFrame(spatial).to_csv(OUT / "SpatialBlockCV.csv", index=False)

# Municipality held-out LightGBM
best_model = models["LightGBM"]
held = []
yt, yp = [], []
for municipality, n in df["municipality"].value_counts().items():
    if n < 30:
        continue
    test = (df["municipality"] == municipality).to_numpy()
    train = ~test
    pipe = Pipeline([("pre", pre), ("model", best_model)])
    pipe.fit(X.iloc[train], y[train])
    pred = pipe.predict(X.iloc[test])
    held.append({"municipality": municipality, "n": int(test.sum()), **metrics(y[test], pred)})
    yt.extend(y[test])
    yp.extend(pred)
pd.DataFrame(held).to_csv(OUT / "MunicipalityHeldOut_LightGBM.csv", index=False)
pd.DataFrame([{
    "Model": "LightGBM",
    "n_municipalities": len(held),
    "n_test_total": len(yt),
    **metrics(np.asarray(yt), np.asarray(yp))
}]).to_csv(OUT / "MunicipalityHeldOut_Overall.csv", index=False)

# Full-fit LightGBM + SHAP
pipe = Pipeline([("pre", pre), ("model", best_model)])
pipe.fit(X, y)
Xt = pipe.named_steps["pre"].transform(X)
feature_names = list(pipe.named_steps["pre"].get_feature_names_out())
model = pipe.named_steps["model"]

rng = np.random.default_rng(42)
idx = rng.choice(np.arange(len(df)), min(5000, len(df)), replace=False)
sv = shap.TreeExplainer(model).shap_values(Xt[idx])
if isinstance(sv, list):
    sv = sv[0]

importance = np.abs(sv).mean(axis=0)
pd.DataFrame({
    "feature": feature_names,
    "mean_abs_SHAP": importance
}).sort_values("mean_abs_SHAP", ascending=False).to_csv(
    OUT / "SHAP_Global.csv", index=False
)

direction = []
sub = df.iloc[idx]
for f in num:
    ids = [i for i, n in enumerate(feature_names) if n.endswith("__" + f)]
    if ids:
        j = ids[0]
        direction.append({
            "predictor": f,
            "spearman_feature_SHAP": spearmanr(sub[f].to_numpy(), sv[:, j]).statistic,
            "mean_abs_SHAP": float(np.abs(sv[:, j]).mean()),
        })
pd.DataFrame(direction).sort_values("mean_abs_SHAP", ascending=False).to_csv(
    OUT / "SHAP_Direction.csv", index=False
)

# Residual spatial diagnostics from 3 km LightGBM OOF predictions
p3 = pred3["LightGBM"]
resid = y - p3
coords = df[["x_utm", "y_utm"]].to_numpy()
nn = NearestNeighbors(n_neighbors=9).fit(coords)
_, inds = nn.kneighbors(coords)
neighbors = inds[:, 1:]
z = resid - resid.mean()
lag = z[neighbors].mean(axis=1)
moran_i = float((z * lag).sum() / (z * z).sum())

rng = np.random.default_rng(123)
perms = []
for _ in range(199):
    zp = rng.permutation(z)
    lp = zp[neighbors].mean(axis=1)
    perms.append(float((zp * lp).sum() / (zp * zp).sum()))
p_value = (1 + sum(abs(v) >= abs(moran_i) for v in perms)) / 200

pd.DataFrame([{
    "Moran_I_k8": moran_i,
    "permutation_p": p_value,
    **metrics(y, p3),
}]).to_csv(OUT / "Residual_Diagnostics.csv", index=False)

# Standardized OLS
Z = pd.DataFrame(StandardScaler().fit_transform(df[num]), columns=num)
dummies = pd.get_dummies(df["WorldCover_cat"], prefix="WC", drop_first=True, dtype=float)
XX = sm.add_constant(pd.concat([Z, dummies], axis=1).astype(float))
ols = sm.OLS(y, XX).fit(cov_type="HC3")
pd.DataFrame({
    "term": ols.params.index,
    "coef": ols.params.values,
    "SE_HC3": ols.bse.values,
    "p_value": ols.pvalues.values,
}).to_csv(OUT / "OLS_Standardized_Coefficients.csv", index=False)

# ------------------------------------------------------------------
# Seasonal robustness sample
# ------------------------------------------------------------------
sdf = pd.read_csv(DATA / "Jolo_Seasonal_Robustness_ModelSample_v04.csv")
swc = sdf["WorldCover_2021"].astype(int).astype(str)
svc = swc.value_counts()
sdf["WorldCover_cat"] = swc.where(~swc.isin(svc[svc < 30].index), "Other")

season_rows, season_spatial, season_shap, season_direction = [], [], [], []

for season in ["MAM", "JJA", "DJF"]:
    target = f"{season}_LST_C"
    obs = f"{season}_valid_obs"
    ndvi = f"{season}_NDVI"
    ndbi = f"{season}_NDBI"

    use = sdf[(sdf[obs] >= 10) & sdf[target].notna()].copy()
    snum = [
        ndvi,
        ndbi,
        "GHSL_built_fraction_30m_corrected",
        "elevation_m",
        "slope_deg",
        "northness",
        "eastness",
        "distance_to_coast_m",
    ]
    S = use[snum + ["WorldCover_cat"]]
    sy = use[target].to_numpy()

    spre = ColumnTransformer([
        ("num", StandardScaler(), snum),
        ("wc", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["WorldCover_cat"]),
    ])
    smodel = LGBMRegressor(
        n_estimators=250, num_leaves=31, learning_rate=0.05,
        subsample=0.85, colsample_bytree=0.85, reg_lambda=1.0,
        random_state=42, verbosity=-1, n_jobs=-1
    )

    random_pred = cross_val_predict(
        Pipeline([("pre", spre), ("model", smodel)]),
        S, sy, cv=KFold(5, shuffle=True, random_state=42), n_jobs=1
    )
    base = {
        "season": season,
        "obs_threshold": 10,
        "n": len(use),
        "mean_LST_C": sy.mean(),
        "median_LST_C": np.median(sy),
        "random_R2": metrics(sy, random_pred)["R2"],
        "random_RMSE": metrics(sy, random_pred)["RMSE"],
        "random_MAE": metrics(sy, random_pred)["MAE"],
    }

    for km in [1, 2, 3, 5]:
        groups = use[f"block{km}km_id"].to_numpy()
        pred = cross_val_predict(
            Pipeline([("pre", spre), ("model", smodel)]),
            S, sy, cv=GroupKFold(5).split(S, sy, groups), n_jobs=1
        )
        mm = metrics(sy, pred)
        season_spatial.append({
            "season": season,
            "block_km": km,
            "n": len(use),
            "n_groups": len(np.unique(groups)),
            **mm
        })
        if km == 3:
            base.update({
                "spatial3km_R2": mm["R2"],
                "spatial3km_RMSE": mm["RMSE"],
                "spatial3km_MAE": mm["MAE"],
            })
    season_rows.append(base)

    # Full fit for SHAP
    spipe = Pipeline([("pre", spre), ("model", smodel)])
    spipe.fit(S, sy)
    SX = spipe.named_steps["pre"].transform(S)
    sfn = list(spipe.named_steps["pre"].get_feature_names_out())
    smdl = spipe.named_steps["model"]
    ii = np.random.default_rng(42).choice(np.arange(len(use)), min(5000, len(use)), replace=False)
    ssv = shap.TreeExplainer(smdl).shap_values(SX[ii])
    if isinstance(ssv, list):
        ssv = ssv[0]
    subu = use.iloc[ii]

    for f in snum:
        ids = [i for i, n in enumerate(sfn) if n.endswith("__" + f)]
        if ids:
            j = ids[0]
            season_shap.append({
                "season": season,
                "predictor": f,
                "mean_abs_SHAP": float(np.abs(ssv[:, j]).mean()),
            })
            season_direction.append({
                "season": season,
                "predictor": f,
                "spearman_feature_SHAP": spearmanr(subu[f].to_numpy(), ssv[:, j]).statistic,
            })

pd.DataFrame(season_rows).to_csv(OUT / "Seasonal_Performance.csv", index=False)
pd.DataFrame(season_spatial).to_csv(OUT / "Seasonal_SpatialBlockCV.csv", index=False)
pd.DataFrame(season_shap).to_csv(OUT / "Seasonal_SHAP.csv", index=False)
pd.DataFrame(season_direction).to_csv(OUT / "Seasonal_SHAP_Direction.csv", index=False)

print(f"Reproduction finished. Outputs written to: {OUT}")
