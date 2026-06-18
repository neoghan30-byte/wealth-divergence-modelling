import pandas as pd
import numpy as np
import pickle
import os
from pathlib import Path

# =====================================================================
# 1. CONFIGURATION
# =====================================================================

BASELINE_V_NUM = "baseline_debug27"       
SENSITIVITY_V_NUM = "sensitivityDebug27"  

# Define paths based on existing structure
project_dir = Path(os.getcwd())
data_dir = project_dir / "data"
graph_dir = data_dir / "graphs"
os.makedirs(graph_dir, exist_ok=True)

print("=== STARTING FINAL METRIC & GRAPHING PIPELINE ===")

# =====================================================================
# 2. LOAD SENSITIVITY RESULTS & GENERATE DYNAMIC TABLES
# =====================================================================
comp_results_path = data_dir / f"comparable_results_{SENSITIVITY_V_NUM}"
print(f"Loading sensitivity results from: {comp_results_path}")

try:
    import zstandard as zstd
    with zstd.open(comp_results_path, "rb") as f:
        master_results = pickle.load(f)
except:
    with open(comp_results_path, "rb") as f:
        master_results = pickle.load(f)

if isinstance(master_results, dict) and "comparable_results" in master_results:
    comp_dict = master_results["comparable_results"]
else:
    comp_dict = master_results

def flatten_results(comparable_results):
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

df = flatten_results(comp_dict)

# --- DYNAMIC GAP CALCULATION ---
# Extract baseline terminal wealths
base_rich = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "80-100") & (df["Metric"] == "terminal") & (df["Scenario"] == "baseline"), "Value"].values[0]
base_med = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "40-59") & (df["Metric"] == "terminal") & (df["Scenario"] == "baseline"), "Value"].values[0]
base_poor = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "0-20") & (df["Metric"] == "terminal") & (df["Scenario"] == "baseline"), "Value"].values[0]

# Calculate Dynamic Baseline Gap
base_gap = base_rich - base_poor

print(f"\n=== CLINICAL BASELINE LOCK (DYNAMIC GAP) ===")
print(f"Baseline Terminal Wealth (80-100): {base_rich:.4f}")
print(f"Baseline Terminal Wealth (0-20):   {base_poor:.4f}")
print(f"Calculated Dynamic Gap:            {base_gap:.4f}\n")

def build_clean_table(scenario_type, param_col_name, param_field):
    scenarios = df.loc[df["Type"] == scenario_type, "Scenario"].unique()
    rows = []
    for sc in scenarios:
        if sc == "baseline": continue
        try:
            r = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "80-100") & (df["Metric"] == "terminal") & (df["Scenario"] == sc), "Value"].values[0]
            m = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "40-59") & (df["Metric"] == "terminal") & (df["Scenario"] == sc), "Value"].values[0]
            p = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "0-20") & (df["Metric"] == "terminal") & (df["Scenario"] == sc), "Value"].values[0]
            
            # Calculate Dynamic Scenario Gap
            g = r - p
            
            param_val = df.loc[(df["Scenario"] == sc) & df[param_field].notnull(), param_field].values
            param_val = param_val[0] if len(param_val) > 0 else np.nan

            # True percentage deltas
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

# Print and Save to CSV
for title, tbl in tables.items():
    if not tbl.empty:
        print(f"=== {title.replace('_', ' ').upper()} ===")
        
        # Format for printing
        print_df = tbl.copy()
        for col in print_df.columns:
            if "%Δ" in col or "Elasticity" in col:
                print_df[col] = print_df[col].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
        print(print_df.to_string(index=False), "\n")
        
        # Save raw numbers to CSV
        csv_path = graph_dir / f"{title}.csv"
        tbl.to_csv(csv_path, index=False)
        print(f"Saved to {csv_path}\n")

# =====================================================================
# 3. LOAD BASELINE STATE & RUN GRAPHS
# =====================================================================
baseline_state_path = data_dir / f"Aggregated_State_{BASELINE_V_NUM}.pkl"
print(f"=== LOADING BASELINE STATE FOR GRAPHS ===")
print(f"Path: {baseline_state_path}")

try:
    try:
        with zstd.open(baseline_state_path, "rb") as f:
            cached = pickle.load(f)
    except:
        with open(baseline_state_path, "rb") as f:
            cached = pickle.load(f)

    aggRes = cached["aggRes"]
    assetResults = cached["assetResults"]
    metric_results = cached["metric_results"]
    households = cached["households"]
    
    
    if "time" in cached:
        time_hist = cached["time"]
    else:
        import datetime as dt
        start = dt.datetime(2000, 1, 1)
        end = dt.datetime(2025, 1, 1)
        time_hist = pd.bdate_range(start=start, end=end).to_pydatetime().tolist()

    print("Running Graphing Pipeline...")
    
  
    from unseperated_main.py import runGraphs
    
    runGraphs(
        aggRes=aggRes,
        assetResults=assetResults,
        time=time_hist,
        households=households,
        graph_dir=graph_dir,
        metric_results=metric_results,
        tablesNeeded=True
    )
    print("=== ALL GRAPHS GENERATED SUCCESSFULLY ===")

except Exception as e:
    print(f"Failed to load baseline state or run graphs: {e}")
    import traceback
    traceback.print_exc()