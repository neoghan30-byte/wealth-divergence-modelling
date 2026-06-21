import os
import re
import pickle
import copy
import numpy as np
import pandas as pd
from pathlib import Path
currentRun = 27
# Import your main file
import unseperated_main

def safe_load(file_path):
    try:
        import zstandard as zstd
        with zstd.open(file_path, "rb") as f:
            return pickle.load(f)
    except Exception:
        with open(file_path, "rb") as f:
            return pickle.load(f)

# =====================================================================
# 1. CONFIGURATION
# =====================================================================

SENSITIVITY_V_NUM = "sensitivityDebug27"
TARGET_PATHS = 5000

cfg = unseperated_main.setup()
data_dir = Path(cfg["data_dir"])
graph_dir = Path(cfg["graph_dir"])
chunk_folder = cfg["chunkFolder"]

print("=== 0. EXTRACTING CONFIGURATION FROM SENSITIVITY TESTS ===")
comp_results_path = data_dir / f"comparable_results_{SENSITIVITY_V_NUM}"
master_results = safe_load(comp_results_path)
comp_dict = master_results.get("comparable_results", master_results)

# Extract correct configuration from the sensitivity tests to ensure perfect alignment
first_scenario = next(iter(comp_dict.values()))
old_inputs = first_scenario.get("inputs", {})
old_inputParameters = old_inputs.get("inputParameters", cfg["inputParameters"])
old_assetWeights = old_inputs.get("assetWeights", cfg["assetWeights"]) 
if "assetWeights" not in old_inputs:
    old_assetWeights = old_inputParameters.get("assetWeights", cfg["assetWeights"])
old_coeffsDict = first_scenario.get("coeffs_dict", None)

if old_coeffsDict is None:
    old_coeffsDict, returnsDict, fullCorr, allTickersOrdered = unseperated_main.getCoeffs(
        cfg["assets"], cfg["assetsCompleted"], cfg["assetsYahoo"], 
        old_assetWeights, cfg["households"], cfg["time"], 
        cfg["corrAbleClasses"], {}, old_inputParameters
    )
else:
    _, returnsDict, fullCorr, allTickersOrdered = unseperated_main.getCoeffs(
        cfg["assets"], cfg["assetsCompleted"], cfg["assetsYahoo"], 
        old_assetWeights, cfg["households"], cfg["time"], 
        cfg["corrAbleClasses"], {}, old_inputParameters
    )

# Determine the correct baseline V_num
existing_baseline_chunks = [
    f for f in os.listdir(chunk_folder) 
    if re.match(rf"^Chunk_Results_{SENSITIVITY_V_NUM}_\d+_\d+\.pkl$", f)
]

if len(existing_baseline_chunks) >= (TARGET_PATHS // old_inputParameters["Chunks"]["chunkSize"]):
    print(f"=== FOUND EXISTING SENSITIVITY BASELINE CHUNKS ===")
    BASELINE_V_NUM = SENSITIVITY_V_NUM
else:
    print(f"=== GENERATING MATCHING BASELINE CHUNKS ===")
    BASELINE_V_NUM = SENSITIVITY_V_NUM + "_baseline"
    old_total_paths = old_inputParameters["Chunks"]["totalPaths"]
    old_inputParameters["Chunks"]["totalPaths"] = TARGET_PATHS
    baseline_bundle_path = data_dir / f"Aggregated_State_baseline_{BASELINE_V_NUM}.pkl"

    unseperated_main.runChunks(
        inputParameters=old_inputParameters,
        coeffsDict=old_coeffsDict,
        fullCorr=fullCorr,
        allTickersOrdered=allTickersOrdered,
        assetWeights=old_assetWeights,
        assets=cfg["assets"],
        assetsCompleted=cfg["assetsCompleted"],
        assetsYahoo=cfg["assetsYahoo"],
        corrAbleClasses=cfg["corrAbleClasses"],
        households=cfg["households"],
        time=cfg["time"],
        returnsDict=returnsDict,
        folder=cfg["folder"],
        V_num=BASELINE_V_NUM,
        testOneChunk=False
    )
    old_inputParameters["Chunks"]["totalPaths"] = old_total_paths


baseline_bundle_path = data_dir / f"Aggregated_State_baseline_{BASELINE_V_NUM}.pkl"
if baseline_bundle_path.exists():
    print(f"=== LOADING CACHED BASELINE FROM {baseline_bundle_path.name} ===")
    with open(baseline_bundle_path, "rb") as f:
        bundle = pickle.load(f)
    
    aggRes = bundle["aggRes"]
    assetResults = bundle["assetResults"]
    metric_results_5k = bundle["metric_results"]
    fullCorr = bundle["fullCorr"]
    allTickersOrdered = bundle["allTickersOrdered"]
    
    print(f"Baseline Terminal Wealth (80-100): {aggRes['portCumR']['80-100'][-1]:.4f}")
    print(f"Baseline Terminal Wealth (0-20):   {aggRes['portCumR']['0-20'][-1]:.4f}")

else:
    print("=== 1. RE-AGGREGATING BASELINE FROM CHUNKS ===")
    state_file = data_dir / f"assetState_{BASELINE_V_NUM}_5k.pkl"
    res_file = data_dir / f"assetStateResults_{BASELINE_V_NUM}_5k.pkl"
    # if state_file.exists(): state_file.unlink()
    # if res_file.exists(): res_file.unlink()

    # Monkey-patch os.listdir to prevent aggregate_to_asset_paths from reading scenario chunks
    original_listdir = os.listdir
    def patched_listdir(path):
        files = original_listdir(path)
        # Only return exact matches for the baseline V_num (rejects scenarios with suffixes like LowerReturns)
        return [f for f in files if re.match(rf"^Chunk_Results_{BASELINE_V_NUM}_\d+_\d+\.pkl$", f) or not f.startswith("Chunk_Results_")]

    os.listdir = patched_listdir
    try:
        assetResults = unseperated_main.aggregate_to_asset_paths(
            TARGET_PATHS, 
            BASELINE_V_NUM, 
            statePath=state_file, 
            resultPath=res_file
        )
    finally:
        os.listdir = original_listdir

    aggRes = unseperated_main.portfolioAggregation(
        old_assetWeights, 
        assetResults, 
        cfg["households"], 
        cfg["assetsCompleted"]
    )
    households = cfg["households"]

    print(f"Baseline Terminal Wealth (80-100): {aggRes['portCumR']['80-100'][-1]:.4f}")
    print(f"Baseline Terminal Wealth (0-20):   {aggRes['portCumR']['0-20'][-1]:.4f}")



    # =====================================================================
    # 2.  CHUNK LOADER FOR METRIC ANALYSIS
    # =====================================================================
    original_sorted_chunk_files = unseperated_main._sorted_chunk_files

    def patched_sorted_chunk_files(chunk_folder, V_num):
        files = original_sorted_chunk_files(chunk_folder, V_num)
        # Ensure strict matching so baseline doesn't pull in scenarios
        files = [f for f in files if re.match(rf"^Chunk_Results_{V_num}_\d+_\d+\.pkl$", f)]
        filtered = []
        for f in files:
            try:
                start_idx = int(f.replace(".pkl", "").split("_")[-2])
                if start_idx < TARGET_PATHS:
                    filtered.append(f)
            except:
                pass
        return filtered

    unseperated_main._sorted_chunk_files = patched_sorted_chunk_files

    # =====================================================================
    # 3. RUN METRIC ANALYSIS ON BASELINE
    # =====================================================================
    print("\n=== 2. RUNNING METRIC ANALYSIS ON MATCHING BASELINE ===")

    metric_results_5k = unseperated_main.get_metric_analysis(
        chunk_folder=chunk_folder,
        coeffs_dict=old_coeffsDict,
        assets_completed=cfg["assetsCompleted"],
        asset_weights=old_assetWeights,
        households=cfg["households"],
        time_hist=cfg["time"],
        V_num=BASELINE_V_NUM,
        percentile_bands=old_inputParameters["percentile_bands"],
        aggRes=aggRes,
        asset_level_res=assetResults
    )

    baseline_bundle_path = data_dir / f"Aggregated_State_baseline_{BASELINE_V_NUM}.pkl"
    with open(baseline_bundle_path, "wb") as f:
        pickle.dump({
            "aggRes": aggRes,
            "assetResults": assetResults,
            "metric_results": metric_results_5k,
            "households": cfg["households"],
            "asset_weights": old_assetWeights,      # household -> assetClass -> ticker -> weight
            "fullCorr": fullCorr,                   # ticker-level correlation matrix (post-modifier)
            "allTickersOrdered": allTickersOrdered, # row/col order matching fullCorr
            "coeffs_dict": old_coeffsDict,
        }, f)
    print(f"Saved baseline bundle to {baseline_bundle_path} "
        f"({baseline_bundle_path.stat().st_size / 1e6:.1f} MB)")
asset_vols = {}
for assetClass in assetResults['sigmaAssetPath']:
    for ticker in assetResults['sigmaAssetPath'][assetClass]:
        sigma_path = assetResults['sigmaAssetPath'][assetClass][ticker]
        asset_vols[ticker] = np.nanmean(sigma_path)   


asset_weights_flat = {
    ticker: w
    for assetClass, tickers in old_assetWeights['80-100'].items()
    for ticker, w in tickers.items()
}

def debug_inputs(bundle_path, household="80-100"):
    with open(bundle_path, "rb") as f:
        bundle = pickle.load(f)
 
    assetResults = bundle["assetResults"]
    asset_weights_nested = bundle["asset_weights"]
    asset_order = bundle["allTickersOrdered"]
    corr_matrix = bundle["fullCorr"]
 
    # Per-ticker vols, as cross_check builds them
    asset_vols = {}
    for assetClass in assetResults["sigmaAssetPath"]:
        for ticker in assetResults["sigmaAssetPath"][assetClass]:
            sigma_path = assetResults["sigmaAssetPath"][assetClass][ticker]
            asset_vols[ticker] = float(np.nanmean(sigma_path))
 
    flat_weights = {
        ticker: w
        for assetClass, tickers in asset_weights_nested[household].items()
        for ticker, w in tickers.items()
    }
 
    print(f"len(asset_order) = {len(asset_order)}")
    print(f"corr_matrix.shape = {corr_matrix.shape}")
    print(f"len(asset_vols) = {len(asset_vols)}")
    print(f"len(flat_weights) = {len(flat_weights)}")
    print()
 
    print("Tickers in asset_order but MISSING from asset_vols (would silently use vol=0):")
    missing_vol = [t for t in asset_order if t not in asset_vols]
    print(f"  {missing_vol}")
    print()
 
    print("Tickers in asset_order but MISSING from flat_weights (would silently use weight=0):")
    missing_w = [t for t in asset_order if t not in flat_weights]
    print(f"  {missing_w}")
    print()
 
    print("Tickers in flat_weights but MISSING from asset_order (silently dropped from formula entirely):")
    missing_order = [t for t in flat_weights if t not in asset_order]
    print(f"  {missing_order}")
    print()
 
    print("Per-ticker check (first 10 by asset_order):")
    for t in asset_order[:10]:
        print(f"  {t!r:30s} weight={flat_weights.get(t, 'MISSING'):>12} "
              f"vol={asset_vols.get(t, 'MISSING')}")
 
    print()
    print("Sample of asset_vols values (sanity check magnitude -- should look like")
    print("annualised vols e.g. 0.1-1.5, NOT tiny daily-scale numbers like 0.01-0.02):")
    for t, v in list(asset_vols.items())[:10]:
        print(f"  {t!r:30s} {v}")
 

import sys
debug_inputs(sys.argv[1] if len(sys.argv) > 1 else baseline_bundle_path)#"Aggregated_State_baseline_sensitivityDebug{currentRun}_baseline.pkl")

def cross_check(aggRes, asset_weights, asset_vols, corr_matrix, asset_order, household, vol_window=252):
    """
    aggRes         : your portfolioAggregation() output dict
    asset_weights  : dict {ticker: weight} for this household (flat, all asset classes)
    asset_vols     : dict {ticker: DAILY vol} -- from sigmaAssetPath, NOT yet annualised
    corr_matrix    : 2D np.ndarray, correlation matrix aligned to asset_order
    asset_order    : list of tickers, same order as corr_matrix rows/cols
    household      : e.g. "80-100"
    """
    # ---- Surface mismatches loudly instead of silently zeroing/dropping ----
    # A previous version of this script silently used .get(t, 0.0), which
    # masked any ticker present in asset_weights but missing from asset_order
    # (it was just dropped from the w' Sigma w sum with no warning at all).
    missing_from_order = [t for t in asset_weights if t not in asset_order]
    weight_in_missing = sum(asset_weights[t] for t in missing_from_order)
    total_weight = sum(asset_weights.values())
    if missing_from_order:
        print(f"  [{household}] WARNING: {len(missing_from_order)} tickers in "
              f"asset_weights are NOT in asset_order and will be EXCLUDED from "
              f"Method 2 entirely: {missing_from_order}")
        print(f"  [{household}] WARNING: those tickers carry "
              f"{weight_in_missing:.4f} of {total_weight:.4f} total weight "
              f"({weight_in_missing/total_weight:.1%}) -- Method 2 below is "
              f"NOT comparable to Method 1 unless this is ~0%.")
 
    # ---- Method 1: direct from simulated portfolio paths ----
    sample_paths = aggRes['portSamplePaths'][household]
    direct_vols = [np.nanstd(p) * np.sqrt(vol_window) for p in sample_paths]  # annualise daily std
    method1_vol = np.nanmean(direct_vols)
 
    # ---- Method 2: w' Sigma w formula ----
    # IMPORTANT: asset_vols (from sigmaAssetPath) are DAILY-scale (e.g.
    # ^GSPC ~ 0.012/day), matching the daily return paths portSamplePaths is
    # also built from. Method 1 annualises by * sqrt(vol_window); Method 2
    # must do the same to the per-asset vols BEFORE building Sigma, or the
    # two methods are off by sqrt(vol_window) (~15.87x for vol_window=252)
    # for no reason related to your actual aggregation code.
    w = np.array([asset_weights.get(t, 0.0) for t in asset_order])
    vols_daily = np.array([asset_vols.get(t, 0.0) for t in asset_order])
    vols_annualised = vols_daily * np.sqrt(vol_window)
    Sigma = np.outer(vols_annualised, vols_annualised) * corr_matrix
    port_var = w @ Sigma @ w
    method2_vol = np.sqrt(port_var) if port_var >= 0 else float('nan')
 
    print(f"=== {household} ===")
    print(f"  Method 1 (direct from simulated portfolio paths): {method1_vol:.4f}")
    print(f"  Method 2 (w' Sigma w formula, your weights/vols/corr, annualised): {method2_vol:.4f}")
    print(f"  Difference: {abs(method1_vol - method2_vol):.4f} "
          f"({abs(method1_vol-method2_vol)/method2_vol:.1%} relative)")
    print(f"  Sum of weights used in Method 2 (asset_order subset only): {w.sum():.4f} "
          f"of {total_weight:.4f} total household weight")
    print()
    return method1_vol, method2_vol
 
 
def load_bundle_and_run(bundle_path, households=None):
    """
    Loads an "Aggregated_State_baseline_*.pkl" bundle (see
    save_baseline_bundle_v2.py) and runs cross_check for each household,
    handling per-ticker vol extraction and weight flattening automatically.
    """
    with open(bundle_path, "rb") as f:
        bundle = pickle.load(f)
 
    aggRes = bundle["aggRes"]
    assetResults = bundle["assetResults"]
    asset_weights_nested = bundle["asset_weights"]   # household -> assetClass -> ticker -> w
    corr_matrix = bundle["fullCorr"]
    asset_order = bundle["allTickersOrdered"]
    if households is None:
        households = bundle["households"]
 
    # Per-ticker vols from sigmaAssetPath (NOT the asset-class-level table)
    asset_vols = {}
    for assetClass in assetResults["sigmaAssetPath"]:
        for ticker in assetResults["sigmaAssetPath"][assetClass]:
            sigma_path = assetResults["sigmaAssetPath"][assetClass][ticker]
            asset_vols[ticker] = float(np.nanmean(sigma_path))
 
    results = {}
    for h in households:
        # Flatten this household's weights from {assetClass: {ticker: w}} to {ticker: w}
        flat_weights = {
            ticker: w
            for assetClass, tickers in asset_weights_nested[h].items()
            for ticker, w in tickers.items()
        }
        results[h] = cross_check(
            aggRes=aggRes,
            asset_weights=flat_weights,
            asset_vols=asset_vols,
            corr_matrix=corr_matrix,
            asset_order=asset_order,
            household=h,
        )
    return results

cross_check(aggRes = aggRes, 
            asset_weights = asset_weights_flat, 
            asset_vols = asset_vols,
            corr_matrix = fullCorr,
            asset_order = allTickersOrdered,
            household = '80-100'
            )

# =====================================================================
# 4. INJECT BASELINE INTO SENSITIVITY RESULTS
# =====================================================================
print("\n=== 3. INJECTING MATCHING BASELINE INTO SENSITIVITY DATA ===")

new_baseline_comp = unseperated_main.get_comparable_results(
    metric_results=metric_results_5k,
    name="baseline",
    inputParameters=old_inputParameters,
    metric_config=cfg["metric_config"],
    coeffsDict=old_coeffsDict,
    sensitivity_results={}
)

comp_dict["baseline"] = new_baseline_comp["baseline"]
import unseperated_main as m
# =====================================================================
comparable_results = m.runSensitivityTests(
        inputParameters=None,
        scenarios=None,
        metric_config=None,
        V_num=f"sensitivityDebug{currentRun}",
        testOneChunk=False,
        selection=None,
        sensitivityResults=new_baseline_comp,
        nPaths=5000
    )
if isinstance(comparable_results, dict) and "comparable_results" in comparable_results:
    comp_dict = comparable_results["comparable_results"]
else:
    comp_dict = comparable_results
print("Keys in comp_dict:", list(comp_dict.keys()))
if "baseline" in comp_dict:
    print("Baseline keys:", list(comp_dict["baseline"].keys()))
# comp_dict = comparable_results
# =====================================================================
# 5. CALCULATE DYNAMIC GAPS & GENERATE TABLES
# =====================================================================
print("\n=== 4. CALCULATING DYNAMIC GAPS & ELASTICITIES ===")

def flatten_results_safe(comparable_results):
    rows = []
    for scenario_name, payload in comparable_results.items():
        inputs = payload.get("inputs", {})
        params = inputs.get("sensitivtyParameters") or {} 
        param_type = params.get("type", "baseline")
        mu_scalar = params.get("muScalar", 1.0)
        vol_scalar = params.get("volScalar", 1.0)
        global_scalar = params.get("Global Scalar", np.nan)
        df_t = params.get("df_t", np.nan)
        std_results = payload.get("standardised_results", {})
        bus_eps_scalar = params.get("busEpsScalar", np.nan)
        alpha_bus = params.get("alphaBus", np.nan)
        std_results = payload.get("standardised_results", {})
        for category, level1_data in std_results.items():
            if not isinstance(level1_data, dict): continue
            for level1_key, level2_data in level1_data.items():
                if not isinstance(level2_data, dict): continue
                for level2_key, metric_data in level2_data.items():
                    if isinstance(metric_data, dict):
                        for metric_name, value in metric_data.items():
                            if metric_name == "raw": continue
                            rows.append({"Scenario": scenario_name, "Type": param_type, "muScalar": mu_scalar, "volScalar": vol_scalar, "Category": category, 
                                         "Level_1": level1_key, "Level_2": level2_key, "Metric": metric_name, "Value": value, "GlobalScalar": global_scalar, 
                                         "df_t": df_t, "busEpsScalar": bus_eps_scalar, "alphaBus": alpha_bus})
                    else:
                        if level2_key == "raw": continue
                        rows.append({"Scenario": scenario_name, "Type": param_type, "muScalar": mu_scalar, "volScalar": vol_scalar, 
                                     "Category": category, "Level_1": level1_key, "Level_2": None, "Metric": level2_key, "Value": metric_data, 
                                     "GlobalScalar": global_scalar, "df_t": df_t, "busEpsScalar": bus_eps_scalar, "alphaBus": alpha_bus})
    df = pd.DataFrame(rows)
    if 'Value' in df.columns: df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    return df

df = flatten_results_safe(comp_dict)
def get_gap(df, scenario):
    return df.loc[
        (df["Scenario"] == scenario) &
        (df["Category"] == "gap_results") &
        (df["Level_1"] == "80-100 vs 0-20") &
        (df["Metric"] == "mean"),
        "Value"
    ].iloc[0]
print(get_gap(df, "baseline"))
import pprint

pprint.pp(
    comp_dict["baseline"]["standardised_results"]["gap_results"]
)
def get_terminal(df, scenario, bucket):
    return df.loc[
        (df["Scenario"] == scenario) &
        (df["Category"] == "mean_household_results") &
        (df["Level_1"] == bucket) &
        (df["Metric"] == "terminal"),
        "Value"
    ].iloc[0]
base_gap  = get_gap(df, "baseline")

base_rich = get_terminal(df, "baseline", "80-100")
base_med  = get_terminal(df, "baseline", "40-59")
base_poor = get_terminal(df, "baseline", "0-20")
# Extract 5k Baseline Terminal Wealths
# base_rich = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "80-100") & (df["Metric"] == "terminal") & (df["Scenario"] == "baseline"), "Value"].values[0]
# base_med = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "40-59") & (df["Metric"] == "terminal") & (df["Scenario"] == "baseline"), "Value"].values[0]
# base_poor = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "0-20") & (df["Metric"] == "terminal") & (df["Scenario"] == "baseline"), "Value"].values[0]

# # DYNAMIC GAP: Rich TW - Poor TW
# base_gap = base_rich - base_poor
print("BASE GAP:", get_gap(df, "baseline"))

for sc in [
    "globalLower20",
    "globalHigher20",
    "df3",
    "df1000"
]:
    print(sc, get_gap(df, sc))
def build_clean_table(scenario_type, param_col_name, param_field):
    scenarios = df.loc[df["Type"] == scenario_type, "Scenario"].unique()
    baseline_param_vals = df.loc[(df["Scenario"] == "baseline") & df[param_field].notnull(), param_field].values
    baseline_param = baseline_param_vals[0] if len(baseline_param_vals) > 0 else 1.0
    rows = []
    for sc in scenarios:
        if sc == "baseline": continue
        if not df.loc[(df["Scenario"] == sc) & df[param_field].notnull()].shape[0]:
            continue
        try:
            r = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "80-100") & (df["Metric"] == "terminal") & (df["Scenario"] == sc), "Value"].values[0]
            m = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "40-59") & (df["Metric"] == "terminal") & (df["Scenario"] == sc), "Value"].values[0]
            p = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "0-20") & (df["Metric"] == "terminal") & (df["Scenario"] == sc), "Value"].values[0]
            
            # g = r - p
            g = get_gap(df, sc)
            param_val = df.loc[(df["Scenario"] == sc) & df[param_field].notnull(), param_field].values
            param_val = param_val[0] if len(param_val) > 0 else np.nan
            
            # g_pct = (g - base_gap) / (0.5 * (abs(g) + abs(base_gap)))
            # r_pct = (r - base_rich) / (0.5 * (abs(r) + abs(base_rich)))
            # m_pct = (m - base_med) / (0.5 * (abs(m) + abs(base_med)))
            # p_pct = (p - base_poor) / (0.5 * (abs(p) + abs(base_poor)))

            # g_pct = (g - base_gap) / (0.5 * (abs(g) + abs(base_gap)))
            # Calculate elasticity using the dynamic baseline parameter
            # input_delta = (param_val - baseline_param) / baseline_param if baseline_param != 0 else (param_val - baseline_param)
            # elas = (g_pct / input_delta) if (input_delta != 0 and not np.isnan(input_delta)) else np.nan

            g_pct = (g - base_gap) / base_gap
            r_pct = (r - base_rich) / base_rich
            m_pct = (m - base_med) / base_med
            p_pct = (p - base_poor) / base_poor
            input_delta = (param_val - baseline_param) / baseline_param if baseline_param != 0 else (param_val - baseline_param)
            elas = (g_pct / input_delta) if (input_delta != 0 and not np.isnan(input_delta)) else np.nan

            rows.append({
                "Scenario": sc,
                param_col_name: param_val,
                "Gap %Δ": g_pct * 100,
                "80-100 TW %Δ": r_pct * 100,
                "40-59 TW %Δ": m_pct * 100,
                "0-20 TW %Δ": p_pct * 100,
                "Gap Elasticity": elas,

            })
        except IndexError:
            continue 
    
    res_df = pd.DataFrame(rows)
    if param_col_name in res_df.columns:
        res_df = res_df.sort_values(param_col_name).reset_index(drop=True)
    return res_df

tables = {
    "Return_Sensitivity": build_clean_table("returns", "Return Scalar", "muScalar"),
    "Volatility_Sensitivity": build_clean_table("volatility", "Vol Scalar", "volScalar"),
    "Correlation_Sensitivity": build_clean_table("correlation", "Global Scalar", "GlobalScalar"),
    "Tail_Risk_Sensitivity": build_clean_table("df_t", "Degrees of Freedom", "df_t"),
    "Business_Wealth_Eps_Sensitivity": build_clean_table("business_wealth", "Business Wealth Eps Scalar", "busEpsScalar"),
    "Business_Wealth_Alpha_Sensitivity": build_clean_table("business_wealth", "Alpha Bus", "alphaBus"),
}


# for title, tbl in tables.items():
#     if not tbl.empty:
#         print(f"=== {title.replace('_', ' ').upper()} ===")
        
#         print_df = tbl.copy()
#         for col in print_df.columns:
#             if "%Δ" in col or "Elasticity" in col:
#                 print_df[col] = print_df[col].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
#             elif np.issubdtype(print_df[col].dtype, np.number):
#                 # Format scalars like 'Degrees of Freedom' to standard strings
#                 print_df[col] = print_df[col].map(lambda x: f"{x:.4g}" if pd.notnull(x) else "")
                
#         print(print_df.to_string(index=False), "\n")
        
#         # Save CSV
#         tbl.to_csv(graph_dir / f"{title}.csv", index=False)
        
        
#         unseperated_main.makeTablePretty(print_df, title.replace('_', ' '), graph_dir)
for title, tbl in tables.items():
    if not tbl.empty:
        print(f"=== {title.replace('_', ' ').upper()} ===")
        
        print_df = tbl.copy()
        for col in print_df.columns:
            if "%Δ" in col or "Elasticity" in col:
                print_df[col] = print_df[col].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
            elif pd.api.types.is_numeric_dtype(print_df[col]):
                # Format scalars like 'Degrees of Freedom' to standard strings using Pandas type checker
                print_df[col] = print_df[col].map(lambda x: f"{x:.4g}" if pd.notnull(x) else "")
                
        print(print_df.to_string(index=False), "\n")
        
        # Save CSV
        tbl.to_csv(graph_dir / f"{title}.csv", index=False)
        
        # Pass the formatted strings to makeTablePretty so it won't multiply by 100
        unseperated_main.makeTablePretty(print_df, title.replace('_', ' '), graph_dir)

# =====================================================================
# 6. RUN ALL NATIVE GRAPHS 
# =====================================================================
print("\n=== 5. RUNNING ALL GRAPHS ===")



# Run  native graphing function. 
print(graph_dir)
print(metric_results_5k.keys())
try:
    unseperated_main.runGraphs(
        aggRes=aggRes,
        assetResults=assetResults,
        time=cfg["time"],
        households=cfg["households"],
        graph_dir=graph_dir,
        metric_results=metric_results_5k,
        tablesNeeded=True,
    )
except Exception:
    import traceback
    traceback.print_exc()
    raise

print("\n=== PIPELINE COMPLETE. CHECK /graphs FOLDER ===")
