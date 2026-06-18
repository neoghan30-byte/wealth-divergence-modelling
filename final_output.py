import os
import pickle
import copy
import numpy as np
import pandas as pd
from pathlib import Path

# Import your main file
import unseperated_main

# =====================================================================
# 1. CONFIGURATION
# =====================================================================
BASELINE_V_NUM = "baseline_debug27"
SENSITIVITY_V_NUM = "sensitivityDebug27"
TARGET_PATHS = 5000

cfg = unseperated_main.setup()
data_dir = Path(cfg["data_dir"])
graph_dir = Path(cfg["graph_dir"])
chunk_folder = cfg["chunkFolder"]

print("=== 1. LOADING & TRUNCATING SAVED BASELINE STATE ===")
baseline_state_path = data_dir / f"Aggregated_State_{BASELINE_V_NUM}.pkl"

with open(baseline_state_path, "rb") as f:
    base_data = pickle.load(f)

aggRes = base_data["aggRes"]
assetResults = base_data["assetResults"]
households = cfg["households"]

# truncate the portfolio paths to 5,000
for h in households:
    aggRes['portSamplePaths'][h] = aggRes['portSamplePaths'][h][:TARGET_PATHS]
    aggRes['portSampleCum'][h] = aggRes['portSampleCum'][h][:TARGET_PATHS]
    aggRes['portSampleSigma'][h] = aggRes['portSampleSigma'][h][:TARGET_PATHS]
    
    # Recompute the means based on the first 5,000 paths
    aggRes['portRet'][h] = np.nanmean(aggRes['portSamplePaths'][h], axis=0)
    aggRes['portCumR'][h] = np.cumprod(1 + aggRes['portRet'][h]) - 1
    aggRes['portSigma'][h] = np.nanmean(aggRes['portSampleSigma'][h], axis=0)

print(f"Truncated 5k Baseline Terminal Wealth (80-100): {aggRes['portCumR']['80-100'][-1]:.4f}")
print(f"Truncated 5k Baseline Terminal Wealth (0-20):   {aggRes['portCumR']['0-20'][-1]:.4f}")

# =====================================================================
# 2.  CHUNK LOADER FOR METRIC ANALYSIS
# =====================================================================

original_sorted_chunk_files = unseperated_main._sorted_chunk_files

def patched_sorted_chunk_files(chunk_folder, V_num):
    files = original_sorted_chunk_files(chunk_folder, V_num)
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
# 3. RUN METRIC ANALYSIS ON 5K BASELINE
# =====================================================================
print("\n=== 2. RUNNING METRIC ANALYSIS ON 5K BASELINE ===")
coeffsDict, returnsDict, fullCorr, allTickersOrdered = unseperated_main.getCoeffs(
    cfg["assets"], cfg["assetsCompleted"], cfg["assetsYahoo"], 
    cfg["assetWeights"], cfg["households"], cfg["time"], 
    cfg["corrAbleClasses"], {}, cfg["inputParameters"]
)

metric_results_5k = unseperated_main.get_metric_analysis(
    chunk_folder=chunk_folder,
    coeffs_dict=coeffsDict,
    assets_completed=cfg["assetsCompleted"],
    asset_weights=cfg["assetWeights"],
    households=cfg["households"],
    time_hist=cfg["time"],
    V_num=BASELINE_V_NUM,
    percentile_bands=cfg["inputParameters"]["percentile_bands"],
    aggRes=aggRes,
    asset_level_res=assetResults
)

# Restore original chunk loader
unseperated_main._sorted_chunk_files = original_sorted_chunk_files

# =====================================================================
# 4. INJECT 5K BASELINE INTO SENSITIVITY RESULTS
# =====================================================================
print("\n=== 3. INJECTING 5K BASELINE INTO SENSITIVITY DATA ===")
comp_results_path = data_dir / f"comparable_results_{SENSITIVITY_V_NUM}.pkl"

with open(comp_results_path, "rb") as f:
    master_results = pickle.load(f)

comp_dict = master_results.get("comparable_results", master_results)

new_baseline_comp = unseperated_main.get_comparable_results(
    metric_results=metric_results_5k,
    name="baseline",
    inputParameters=cfg["inputParameters"],
    metric_config=cfg["metric_config"],
    coeffsDict=coeffsDict,
    sensitivity_results={}
)

comp_dict["baseline"] = new_baseline_comp["baseline"]

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
        
        for category, level1_data in std_results.items():
            if not isinstance(level1_data, dict): continue
            for level1_key, level2_data in level1_data.items():
                if not isinstance(level2_data, dict): continue
                for level2_key, metric_data in level2_data.items():
                    if isinstance(metric_data, dict):
                        for metric_name, value in metric_data.items():
                            if metric_name == "raw": continue
                            rows.append({"Scenario": scenario_name, "Type": param_type, "muScalar": mu_scalar, "volScalar": vol_scalar, "Category": category, "Level_1": level1_key, "Level_2": level2_key, "Metric": metric_name, "Value": value, "GlobalScalar": global_scalar, "df_t": df_t})
                    else:
                        if level2_key == "raw": continue
                        rows.append({"Scenario": scenario_name, "Type": param_type, "muScalar": mu_scalar, "volScalar": vol_scalar, "Category": category, "Level_1": level1_key, "Level_2": None, "Metric": level2_key, "Value": metric_data, "GlobalScalar": global_scalar, "df_t": df_t})
    df = pd.DataFrame(rows)
    if 'Value' in df.columns: df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    return df

df = flatten_results_safe(comp_dict)

# Extract 5k Baseline Terminal Wealths
base_rich = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "80-100") & (df["Metric"] == "terminal") & (df["Scenario"] == "baseline"), "Value"].values[0]
base_med = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "40-59") & (df["Metric"] == "terminal") & (df["Scenario"] == "baseline"), "Value"].values[0]
base_poor = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "0-20") & (df["Metric"] == "terminal") & (df["Scenario"] == "baseline"), "Value"].values[0]

# DYNAMIC GAP: Rich TW - Poor TW
base_gap = base_rich - base_poor

def build_clean_table(scenario_type, param_col_name, param_field):
    scenarios = df.loc[df["Type"] == scenario_type, "Scenario"].unique()
    rows = []
    for sc in scenarios:
        if sc == "baseline": continue
        try:
            r = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "80-100") & (df["Metric"] == "terminal") & (df["Scenario"] == sc), "Value"].values[0]
            m = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "40-59") & (df["Metric"] == "terminal") & (df["Scenario"] == sc), "Value"].values[0]
            p = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "0-20") & (df["Metric"] == "terminal") & (df["Scenario"] == sc), "Value"].values[0]
            
            g = r - p
            param_val = df.loc[(df["Scenario"] == sc) & df[param_field].notnull(), param_field].values
            param_val = param_val[0] if len(param_val) > 0 else np.nan

            g_pct = (g - base_gap) / (0.5 * (abs(g) + abs(base_gap)))
            r_pct = (r - base_rich) / (0.5 * (abs(r) + abs(base_rich)))
            m_pct = (m - base_med) / (0.5 * (abs(m) + abs(base_med)))
            p_pct = (p - base_poor) / (0.5 * (abs(p) + abs(base_poor)))

            input_delta = (param_val - 1.0) if scenario_type in ["returns", "volatility"] else np.nan
            elas = (g_pct / input_delta) if (input_delta != 0 and not np.isnan(input_delta)) else np.nan

            rows.append({
                "Scenario": sc,
                param_col_name: param_val,
                "Gap %Δ": g_pct * 100.0,
                "Gap Elasticity": elas,
                "80-100 TW %Δ": r_pct * 100.0,
                "40-59 TW %Δ": m_pct * 100.0,
                "0-20 TW %Δ": p_pct * 100.0
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
    "Tail_Risk_Sensitivity": build_clean_table("df_t", "Degrees of Freedom", "df_t")
}

for title, tbl in tables.items():
    if not tbl.empty:
        print(f"=== {title.replace('_', ' ').upper()} ===")
        
        
        print_df = tbl.copy()
        for col in print_df.columns:
            if "%Δ" in col or "Elasticity" in col:
                print_df[col] = print_df[col].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
        print(print_df.to_string(index=False), "\n")
        
        # Save CSV
        tbl.to_csv(graph_dir / f"{title}.csv", index=False)
        
       
        unseperated_main.makeTablePretty(tbl, title.replace('_', ' '), graph_dir)

# =====================================================================
# 6. RUN ALL NATIVE GRAPHS 
# =====================================================================
print("\n=== 5. RUNNING ALL GRAPHS ===")



# Run your native graphing function. 
# metric_results_5k is passed pristine, so no data is lost.
unseperated_main.runGraphs(
    aggRes=aggRes,
    assetResults=assetResults,
    time=cfg["time"],
    households=cfg["households"],
    graph_dir=graph_dir,
    metric_results=metric_results_5k,
    tablesNeeded=True
)

print("\n=== PIPELINE COMPLETE. CHECK /graphs FOLDER ===")