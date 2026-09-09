"""Version 2 EMS robustness and matched-transfer rerun.

This script extends the Version 1 reproduction workflow with the analyses used
in the Environmental Modelling & Software manuscript:

  * fold-wise SHAP under 1, 2, 3 and 5 km spatial blocking;
  * municipality-held-out prediction + attribution transfer;
  * 3 km block-origin perturbation;
  * cross-model (LightGBM, XGBoost, random forest) stress tests;
  * dominant-predictor ablation;
  * LightGBM seed sensitivity;
  * seasonal 3 km matched SHAP evaluation when the frozen seasonal table is
    available.

Frozen manuscript-supporting outputs are stored under ``results/v2_ems``.
This rerun writes to ``reproduced_results/v2_ems`` and never overwrites the
frozen archive.
"""
from __future__ import annotations

from pathlib import Path
import itertools
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
import shap

SEED = 42
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "derived"
OUT = ROOT / "reproduced_results" / "v2_ems"
OUT.mkdir(parents=True, exist_ok=True)

MAIN_FILE = DATA / "Jolo_Modeling_Sample_Local_v03.csv"
SEASONAL_FILE = DATA / "Jolo_Seasonal_Robustness_ModelSample_v04.csv"

CONTINUOUS = [
    "NDVI_MAM_median",
    "NDBI_MAM_median",
    "GHSL_built_local_fraction",
    "elevation_m",
    "slope_deg",
    "northness",
    "eastness",
    "distance_to_coast_m",
]
GROUP_ORDER = CONTINUOUS + ["WorldCover"]


def metrics(y_true, y_pred):
    return {
        "R2": float(r2_score(y_true, y_pred)),
        "RMSE": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
    }


def kendall_w(rank_matrix: np.ndarray) -> float:
    """Kendall's coefficient of concordance for rows=judges/models, cols=items."""
    r = np.asarray(rank_matrix, dtype=float)
    if r.ndim != 2 or r.shape[0] < 2 or r.shape[1] < 2:
        return np.nan
    m, n = r.shape
    # Rank each row so ties are handled consistently.
    rr = np.vstack([rankdata(row, method="average") for row in r])
    col_sums = rr.sum(axis=0)
    s = np.sum((col_sums - col_sums.mean()) ** 2)
    # Tie correction across rows.
    tie_term = 0.0
    for row in rr:
        _, counts = np.unique(row, return_counts=True)
        tie_term += np.sum(counts**3 - counts)
    denom = m * m * (n**3 - n) - m * tie_term
    return float(12.0 * s / denom) if denom > 0 else np.nan


def pairwise_rank_stats(rank_table: pd.DataFrame):
    vals = rank_table.to_numpy(dtype=float)
    rhos = []
    for i, j in itertools.combinations(range(len(vals)), 2):
        rho = spearmanr(vals[i], vals[j]).statistic
        if np.isfinite(rho):
            rhos.append(float(rho))
    return {
        "Kendall_W": kendall_w(vals),
        "pairwise_rho_mean": float(np.mean(rhos)) if rhos else np.nan,
        "pairwise_rho_median": float(np.median(rhos)) if rhos else np.nan,
        "pairwise_rho_min": float(np.min(rhos)) if rhos else np.nan,
    }


def prepare_worldcover(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    wc = df["WorldCover_2021"].astype(int).astype(str)
    vc = wc.value_counts()
    df["WorldCover_cat"] = wc.where(~wc.isin(vc[vc < 30].index), "Other")
    return df


def make_preprocessor(features):
    cont = [f for f in features if f != "WorldCover_cat"]
    return ColumnTransformer([
        ("num", StandardScaler(), cont),
        ("wc", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["WorldCover_cat"]),
    ])


def model_factory(name: str, seed: int = SEED):
    if name == "LightGBM":
        return LGBMRegressor(
            n_estimators=250, num_leaves=31, learning_rate=0.05,
            subsample=0.85, colsample_bytree=0.85, reg_lambda=1.0,
            random_state=seed, verbosity=-1, n_jobs=-1,
        )
    if name == "XGBoost":
        return XGBRegressor(
            n_estimators=250, max_depth=6, learning_rate=0.05,
            subsample=0.85, colsample_bytree=0.85, reg_lambda=1.0,
            objective="reg:squarederror", n_jobs=-1, random_state=seed,
        )
    if name == "RandomForest":
        return RandomForestRegressor(
            n_estimators=250, min_samples_leaf=2, max_features=0.8,
            n_jobs=-1, random_state=seed,
        )
    raise ValueError(name)


def grouped_shap(pipe: Pipeline, X_test: pd.DataFrame):
    Xt = pipe.named_steps["pre"].transform(X_test)
    names = list(pipe.named_steps["pre"].get_feature_names_out())
    model = pipe.named_steps["model"]
    sv = shap.TreeExplainer(model).shap_values(Xt)
    if isinstance(sv, list):
        sv = sv[0]
    sv = np.asarray(sv)

    result = {}
    # Continuous variables map one-to-one after preprocessing.
    for raw in [c for c in X_test.columns if c != "WorldCover_cat"]:
        ids = [i for i, n in enumerate(names) if n.endswith("__" + raw)]
        if ids:
            v = sv[:, ids[0]]
            result[raw] = {
                "importance": float(np.abs(v).mean()),
                "direction_rho": float(spearmanr(X_test[raw].to_numpy(), v).statistic),
            }
    # WorldCover is grouped over one-hot components.
    wc_ids = [i for i, n in enumerate(names) if n.startswith("wc__")]
    if wc_ids:
        grouped = sv[:, wc_ids].sum(axis=1)
        result["WorldCover"] = {
            "importance": float(np.abs(sv[:, wc_ids]).sum(axis=1).mean()),
            "direction_rho": np.nan,
        }
    return result


def evaluate_groups(df, groups, model_name="LightGBM", features=None, seed=SEED):
    if features is None:
        features = CONTINUOUS + ["WorldCover_cat"]
    X = df[features]
    y = df["LST_MAM_median_C"].to_numpy()
    cv = GroupKFold(5)
    oof = np.full(len(df), np.nan)
    perf_rows, shap_rows = [], []

    for fold, (tr, te) in enumerate(cv.split(X, y, groups), 1):
        pipe = Pipeline([
            ("pre", make_preprocessor(features)),
            ("model", model_factory(model_name, seed=seed)),
        ])
        pipe.fit(X.iloc[tr], y[tr])
        pred = pipe.predict(X.iloc[te])
        oof[te] = pred
        perf_rows.append({"fold": fold, "n_train": len(tr), "n_test": len(te), **metrics(y[te], pred)})
        g = grouped_shap(pipe, X.iloc[te])
        for predictor, d in g.items():
            shap_rows.append({
                "fold": fold,
                "predictor": predictor,
                "mean_abs_SHAP": d["importance"],
                "direction_rho": d["direction_rho"],
            })

    shp = pd.DataFrame(shap_rows)
    shp["rank"] = shp.groupby("fold")["mean_abs_SHAP"].rank(method="average", ascending=False)
    rank_pivot = shp.pivot(index="fold", columns="predictor", values="rank")
    return metrics(y, oof), pd.DataFrame(perf_rows), shp, pairwise_rank_stats(rank_pivot)


def block_origin_groups(df, dx=0.0, dy=0.0, block_m=3000.0):
    bx = np.floor((df["x_utm"].to_numpy() + dx) / block_m).astype(int)
    by = np.floor((df["y_utm"].to_numpy() + dy) / block_m).astype(int)
    return np.array([f"{x}_{y}" for x, y in zip(bx, by)], dtype=object)


def run_multiscale(df):
    rows = []
    for km in [1, 2, 3, 5]:
        groups = df[f"block{km}km_id"].to_numpy()
        overall, folds, shp, stab = evaluate_groups(df, groups, "LightGBM")
        folds.insert(0, "block_km", km)
        shp.insert(0, "block_km", km)
        folds.to_csv(OUT / f"V2_{km}km_FoldPerformance.csv", index=False)
        shp.to_csv(OUT / f"V2_{km}km_FoldSHAP.csv", index=False)
        rows.append({"block_km": km, "n_blocks": len(np.unique(groups)), **overall, **stab})
    pd.DataFrame(rows).to_csv(OUT / "V2_Multiscale_ExplanationStability_Summary.csv", index=False)


def run_block_origin(df):
    summaries, fold_all = [], []
    for dx, dy in [(0, 0), (1500, 0), (0, 1500), (1500, 1500)]:
        groups = block_origin_groups(df, dx, dy)
        overall, folds, shp, stab = evaluate_groups(df, groups, "LightGBM")
        folds.insert(0, "offset_y_m", dy)
        folds.insert(0, "offset_x_m", dx)
        fold_all.append(folds)
        summaries.append({
            "offset_x_m": dx, "offset_y_m": dy,
            "n_blocks": len(np.unique(groups)), **overall,
            "n_models": 5, "n_predictors": len(GROUP_ORDER), **stab,
        })
    pd.concat(fold_all, ignore_index=True).to_csv(OUT / "V2_BlockOrigin_Sensitivity_ByFold.csv", index=False)
    pd.DataFrame(summaries).to_csv(OUT / "V2_BlockOrigin_Sensitivity_Summary.csv", index=False)


def run_cross_model(df):
    groups = df["block3km_id"].to_numpy()
    perf, shap_all, stability = [], [], []
    for name in ["LightGBM", "XGBoost", "RandomForest"]:
        overall, folds, shp, stab = evaluate_groups(df, groups, name)
        perf.append({"model": name, **overall})
        shp.insert(0, "model", name)
        shap_all.append(shp)
        stability.append({"model": name, "n_models": 5, "n_predictors": len(GROUP_ORDER), **stab})
    pd.DataFrame(perf).to_csv(OUT / "V2_CrossModel_3km_Performance.csv", index=False)
    pd.concat(shap_all, ignore_index=True).to_csv(OUT / "V2_CrossModel_SHAP_3km_ByFold.csv", index=False)
    pd.DataFrame(stability).to_csv(OUT / "V2_CrossModel_WithinModel_Stability.csv", index=False)

    # Mean ranks and cross-model rank agreement.
    allsh = pd.concat(shap_all, ignore_index=True)
    mean_imp = allsh.groupby(["model", "predictor"], as_index=False)["mean_abs_SHAP"].mean()
    mean_imp["rank"] = mean_imp.groupby("model")["mean_abs_SHAP"].rank(ascending=False, method="average")
    mean_imp.to_csv(OUT / "V2_CrossModel_MeanImportance.csv", index=False)
    piv = mean_imp.pivot(index="model", columns="predictor", values="rank")
    rr = []
    for a, b in itertools.combinations(piv.index, 2):
        rho = spearmanr(piv.loc[a], piv.loc[b]).statistic
        rr.append({"model_a": a, "model_b": b, "spearman_rho": rho})
    pd.DataFrame(rr).to_csv(OUT / "V2_CrossModel_RankAgreement.csv", index=False)


def run_ablation(df):
    groups = df["block3km_id"].to_numpy()
    configs = {
        "full": CONTINUOUS,
        "without_elevation": [f for f in CONTINUOUS if f != "elevation_m"],
        "without_elevation_and_NDVI": [f for f in CONTINUOUS if f not in {"elevation_m", "NDVI_MAM_median"}],
    }
    summary, fold_shap = [], []
    for label, cont in configs.items():
        features = cont + ["WorldCover_cat"]
        overall, folds, shp, stab = evaluate_groups(df, groups, "LightGBM", features=features)
        shp.insert(0, "configuration", label)
        fold_shap.append(shp)
        summary.append({
            "configuration": label,
            "n_predictors": len(cont) + 1,
            **overall,
            "n_models": 5,
            **stab,
        })
    pd.concat(fold_shap, ignore_index=True).to_csv(OUT / "V2_Ablation_ExplanationStability_ByFold.csv", index=False)
    pd.DataFrame(summary).to_csv(OUT / "V2_Ablation_ExplanationStability_Summary.csv", index=False)


def run_lomo(df):
    features = CONTINUOUS + ["WorldCover_cat"]
    X = df[features]
    y = df["LST_MAM_median_C"].to_numpy()

    # Full-island reference rank.
    ref = Pipeline([("pre", make_preprocessor(features)), ("model", model_factory("LightGBM"))])
    ref.fit(X, y)
    full = grouped_shap(ref, X)
    ref_rank = pd.Series({k: v["importance"] for k, v in full.items()}).rank(ascending=False)

    rows, shp_rows, yt, yp = [], [], [], []
    for municipality in sorted(df["municipality"].dropna().unique()):
        te = (df["municipality"] == municipality).to_numpy()
        if te.sum() < 30:
            continue
        tr = ~te
        pipe = Pipeline([("pre", make_preprocessor(features)), ("model", model_factory("LightGBM"))])
        pipe.fit(X.iloc[tr], y[tr])
        pred = pipe.predict(X.iloc[te])
        yt.extend(y[te]); yp.extend(pred)
        g = grouped_shap(pipe, X.iloc[te])
        imp = pd.Series({k: v["importance"] for k, v in g.items()})
        rank = imp.rank(ascending=False)
        common = rank.index.intersection(ref_rank.index)
        sim = float(spearmanr(rank[common], ref_rank[common]).statistic)
        rows.append({"municipality": municipality, "n": int(te.sum()), **metrics(y[te], pred), "rank_similarity_to_full": sim})
        for k, v in g.items():
            shp_rows.append({"municipality": municipality, "predictor": k, "mean_abs_SHAP": v["importance"], "direction_rho": v["direction_rho"], "rank": rank[k]})

    m = pd.DataFrame(rows)
    s = pd.DataFrame(shp_rows)
    m.to_csv(OUT / "V2_LOMO_PredictionAttribution.csv", index=False)
    s.to_csv(OUT / "V2_LOMO_SHAP.csv", index=False)
    pooled = {"n_municipalities": len(m), **metrics(np.asarray(yt), np.asarray(yp))}
    if len(m) >= 3:
        pooled["rho_R2_vs_rank_similarity"] = float(spearmanr(m["R2"], m["rank_similarity_to_full"]).statistic)
        pooled["p_R2_vs_rank_similarity"] = float(spearmanr(m["R2"], m["rank_similarity_to_full"]).pvalue)
    pd.DataFrame([pooled]).to_csv(OUT / "V2_LOMO_Summary.csv", index=False)

    rp = s.pivot(index="municipality", columns="predictor", values="rank")
    pd.DataFrame([{**pairwise_rank_stats(rp), "n_models": len(rp), "n_predictors": rp.shape[1]}]).to_csv(
        OUT / "V2_LOMO_ExplanationStability.csv", index=False
    )


def run_seed_sensitivity(df):
    features = CONTINUOUS + ["WorldCover_cat"]
    X = df[features]
    y = df["LST_MAM_median_C"].to_numpy()
    rows = []
    for seed in range(10):
        pipe = Pipeline([("pre", make_preprocessor(features)), ("model", model_factory("LightGBM", seed=seed))])
        pipe.fit(X, y)
        g = grouped_shap(pipe, X)
        imp = pd.Series({k: v["importance"] for k, v in g.items()})
        ranks = imp.rank(ascending=False)
        for k in imp.index:
            rows.append({"seed": seed, "predictor": k, "mean_abs_SHAP": imp[k], "rank": ranks[k]})
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "V2_LightGBM_Seed_SHAP_Importance.csv", index=False)
    rp = d.pivot(index="seed", columns="predictor", values="rank")
    pd.DataFrame([{**pairwise_rank_stats(rp), "n_seeds": len(rp), "n_predictors": rp.shape[1]}]).to_csv(
        OUT / "V2_LightGBM_Seed_ExplanationStability.csv", index=False
    )


def run_seasonal():
    if not SEASONAL_FILE.exists():
        print(f"Seasonal file not found; skipping: {SEASONAL_FILE}")
        return
    sdf = prepare_worldcover(pd.read_csv(SEASONAL_FILE))
    rows = []
    for season in ["MAM", "JJA", "DJF"]:
        target = f"{season}_LST_C"
        obs = f"{season}_valid_obs"
        ndvi = f"{season}_NDVI"
        ndbi = f"{season}_NDBI"
        use = sdf[(sdf[obs] >= 10) & sdf[target].notna()].copy()
        use = use.rename(columns={target: "LST_MAM_median_C", ndvi: "NDVI_MAM_median", ndbi: "NDBI_MAM_median"})
        # Prefer the independently audited seasonal built-fraction field.
        if "GHSL_built_fraction_30m_corrected" in use.columns:
            use["GHSL_built_local_fraction"] = use["GHSL_built_fraction_30m_corrected"]
        groups = use["block3km_id"].to_numpy()
        overall, folds, shp, stab = evaluate_groups(use, groups, "LightGBM")
        folds.insert(0, "season", season)
        shp.insert(0, "season", season)
        folds.to_csv(OUT / f"V2_Seasonal_{season}_3km_FoldPerformance.csv", index=False)
        shp.to_csv(OUT / f"V2_Seasonal_{season}_3km_FoldSHAP.csv", index=False)
        rows.append({"season": season, "n": len(use), **overall, **stab})
    pd.DataFrame(rows).to_csv(OUT / "V2_Seasonal_ExplanationStability_Summary.csv", index=False)


def main():
    if not MAIN_FILE.exists():
        raise FileNotFoundError(f"Missing frozen main sample: {MAIN_FILE}")
    df = prepare_worldcover(pd.read_csv(MAIN_FILE))
    required = set(CONTINUOUS + ["LST_MAM_median_C", "municipality", "x_utm", "y_utm"] + [f"block{k}km_id" for k in [1,2,3,5]])
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing expected fields: {missing}")

    print(f"Loaded {len(df):,} main samples")
    run_multiscale(df)
    run_lomo(df)
    run_block_origin(df)
    run_cross_model(df)
    run_ablation(df)
    run_seed_sensitivity(df)
    run_seasonal()
    print(f"Version 2 outputs written to: {OUT}")


if __name__ == "__main__":
    main()
