import os
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from pathlib import Path

# =====================================================================
# 1. SETUP PATHS
# =====================================================================
project_dir = Path(os.getcwd())
data_dir = project_dir / "data"
graph_dir = data_dir / "graphs"
os.makedirs(graph_dir, exist_ok=True)

BASELINE_V_NUM = "baseline_debug27"
SENSITIVITY_V_NUM = "sensitivityDebug27"

print("=== STARTING UNIFIED TABLE & GRAPH PIPELINE ===")

# =====================================================================
# 2. SENSITIVITY TABLES (TEXT, CSV, AND PNG)
# =====================================================================
comp_results_path = data_dir / f"comparable_results_{SENSITIVITY_V_NUM}"
print(f"\nLoading sensitivity results from: {comp_results_path}")

try:
    import zstandard as zstd
    with zstd.open(comp_results_path, "rb") as f:
        master_results = pickle.load(f)
except:
    with open(comp_results_path, "rb") as f:
        master_results = pickle.load(f)

comp_dict = master_results.get("comparable_results", master_results)

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

# Dynamic Gap Calculation
base_rich = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "80-100") & (df["Metric"] == "terminal") & (df["Scenario"] == "baseline"), "Value"].values[0]
base_med = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "40-59") & (df["Metric"] == "terminal") & (df["Scenario"] == "baseline"), "Value"].values[0]
base_poor = df.loc[(df["Category"] == "mean_household_results") & (df["Level_1"] == "0-20") & (df["Metric"] == "terminal") & (df["Scenario"] == "baseline"), "Value"].values[0]
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


from unseperated_main import makeTablePretty

for title, tbl in tables.items():
    if not tbl.empty:
        print(f"\n=== {title.replace('_', ' ').upper()} ===")
        
        # 1. Print to Console
        print_df = tbl.copy()
        for col in print_df.columns:
            if "%Δ" in col or "Elasticity" in col:
                print_df[col] = print_df[col].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
        print(print_df.to_string(index=False))
        
        # 2. Save to CSV
        csv_path = graph_dir / f"{title}.csv"
        tbl.to_csv(csv_path, index=False)
        
        # 3. Save to PNG using your function
        try:
            makeTablePretty(tbl, title.replace('_', ' '), str(graph_dir), fontsize=12)
        except Exception as e:
            print(f"Failed to generate PNG for {title}: {e}")

# =====================================================================
# 3. BASELINE GRAPHS
# =====================================================================
baseline_state_path = data_dir / f"Aggregated_State_{BASELINE_V_NUM}.pkl"
print(f"\n=== LOADING BASELINE STATE FOR GRAPHS ===")
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
    time_hist = pd.bdate_range(start=dt.datetime(2000, 1, 1), end=dt.datetime(2025, 1, 1)).to_pydatetime().tolist()

# Styling
graphFigSize = (14,6)
titleWeight = 'normal'
householdDisplayLabels = {"0-20": "0–20th Income Percentile", "40-59": "40–59th Income Percentile", "80-100": "80–100th Income Percentile"}
assetClassColours = {"Equities": "tab:red", "Bonds Short": "tab:blue", "Bonds Long": "tab:purple", "Property": "tab:orange", "Deposits": "tab:green", "Business Wealth": "#FFD700"}
houseHoldAssetsColours = {"80-100": "tab:red", "0-20": "tab:blue", "40-59": "tab:green"}
houseHoldAssetsColoursCumPaths = {"80-100": "crimson", "0-20": "mediumblue", "40-59": "green"}

from unseperated_main import (
    householdVolatilityPlot, assetClassVolatilityBar, plot_wealth_gap_dist,
    plot_monte_carlo_convergence, backtest_distribution_plot, CRPS_bar_chart,
    getHeatMap, getWeightsTable, householdWeightsBar
)

def run_safe(name, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
        print(f"[SUCCESS] {name}")
    except Exception as e:
        print(f"[FAILED]  {name} -> {e}")

# --- CUMULATIVE PATHS PLOT  ---
def custom_cum_paths_plot(assetRes, time, graphFigSize, folder):
    plt.figure(figsize=graphFigSize)
    x = pd.to_datetime(time[-len(assetRes['portCumR']['80-100']):])
    
    # Custom Alphas: Drastically reduce 0-20 so it doesn't dominate
    alphas = {"80-100": 0.3, "40-59": 0.2, "0-20": 0.03} 
    
    # Plot 0-20 first so it sits in the background
    plot_order = ["0-20", "40-59", "80-100"]
    
    for h in plot_order:
        for path in assetRes['portSampleCum'][h]:
            plt.plot(x, path*100, color=houseHoldAssetsColoursCumPaths[h], alpha=alphas[h], linewidth=0.8)
            
    # Dummy lines for the legend
    for h in ["80-100", "40-59", "0-20"]:
        plt.plot([], [], color=houseHoldAssetsColoursCumPaths[h], label=householdDisplayLabels[h], linewidth=4)
        
    plt.title("Household Portfolio: Cumulative Return Paths", weight='normal')
    plt.xlabel("Date")
    plt.ylabel("Cumulative Return (%)")
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(100.0))
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title="HH Income Group")
    plt.savefig(os.path.join(folder, "cumRpaths_adjusted.png"), dpi=600)
    plt.close()

# ---  MEAN PATH PLOT  ---
def plotMeanPath_fixed(meanPathDict, households, time, householdDisplayLabels, graphFigSize, houseHoldAssetsColours, titleWeight, folder):
    plt.figure(figsize=graphFigSize)
    x = pd.to_datetime(time[-len(meanPathDict[households[0]]):])
    for h in households:
        plt.plot(x, meanPathDict[h]*100, color=houseHoldAssetsColours[h], label=f"{householdDisplayLabels[h]}", linewidth=2)
    plt.title("Cumulative Returns: Mean Household Path", weight=titleWeight)
    plt.xlabel("Date")
    plt.ylabel("Cumulative Return (%)")
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(100.0))
    plt.legend(title="HH Income Group", loc="upper left")
    plt.grid(True)
    plt.savefig(os.path.join(folder, "meanPath.png"), dpi=600)
    plt.close()

print("\n=== GENERATING ALL GRAPHS ===")
run_safe("Cumulative Return Paths (Adjusted Alpha)", custom_cum_paths_plot, aggRes, time_hist, graphFigSize, str(graph_dir))
run_safe("Mean Path", plotMeanPath_fixed, aggRes['portCumR'], households, time_hist, householdDisplayLabels, graphFigSize, houseHoldAssetsColours, titleWeight, str(graph_dir))
run_safe("Household Volatility", householdVolatilityPlot, graphFigSize, houseHoldAssetsColours, aggRes, time_hist, str(graph_dir))
run_safe("Asset Class Volatility", assetClassVolatilityBar, graphFigSize, assetResults, assetClassColours, titleWeight, str(graph_dir))

try:
    pairs = metric_results["results"]["gap_results"]["raw"]["pairs"]
    summary_df = metric_results["results"]["gap_results"]["raw"]["summary_df"]
    prob_positive = metric_results["results"]["gap_results"]["raw"]["prob_positive"]
    run_safe("Wealth Gap Distribution", plot_wealth_gap_dist, pairs, summary_df, prob_positive, str(graph_dir))
except KeyError: print("[FAILED] Wealth Gap Distribution")

try:
    convergence_df = metric_results["validation"]["convergence_results"]["raw"]["convergence_df"]
    path_number = metric_results["validation"]["convergence_results"]["raw"]["path_number"]
    run_safe("Monte Carlo Convergence", plot_monte_carlo_convergence, convergence_df, str(graph_dir), households, path_number)
except KeyError: print("[FAILED] Monte Carlo Convergence")

try:
    backtest_df = metric_results["validation"]["back_test_results"]["raw"]["backtest_df"]
    backtest_raw = metric_results["validation"]["back_test_results"]["raw"]["backtest_raw"]
    sim_low_pct = metric_results["validation"]["back_test_results"]["raw"]["sim_low_pct"]
    sim_high_pct = metric_results["validation"]["back_test_results"]["raw"]["sim_high_pct"]
    run_safe("Backtest Distributions", backtest_distribution_plot, backtest_df, households, backtest_raw, sim_low_pct, sim_high_pct, path_number, str(graph_dir))
except KeyError: print("[FAILED] Backtest Distributions")

try:
    crps_scores = metric_results["validation"]["crps_results"]["raw"]["crps_scores"]
    crps_per_window = metric_results["validation"]["crps_results"]["raw"]["crps_per_window"]
    run_safe("CRPS Bar Chart", CRPS_bar_chart, crps_scores, crps_per_window, str(graph_dir))
except KeyError: print("[FAILED] CRPS Bar Chart")

try:
    coverage_df = metric_results["validation"]["band_results"]["raw"]["coverage_df"]
    coverage = metric_results["validation"]["band_results"]["raw"]["coverage_raw"]
    sim_one_year = metric_results["validation"]["band_results"]["raw"]["sim_horizon"]
    hist_one_year = metric_results["validation"]["band_results"]["raw"]["hist_horizon"]
    band_names = metric_results["validation"]["band_results"]["raw"]["band_names"]
    expected = metric_results["validation"]["band_results"]["raw"]["expected"]
    run_safe("Multi-Band Heatmap", getHeatMap, households, coverage_df, coverage, sim_one_year, hist_one_year, band_names, expected, str(graph_dir))
except KeyError: print("[FAILED] Multi-Band Heatmap")

try:
    asset_weight_inputs = metric_results["inputs"]
    run_safe("Weights Table", getWeightsTable, asset_weight_inputs, 14)
except KeyError: print("[FAILED] Weights Table")

try:
    asset_weights_raw = metric_results["inputs"]["assetWeights"]
    assets = metric_results["inputs"]["assets"]
    run_safe("Household Weights Bar", householdWeightsBar, asset_weights_raw, assets, households, houseHoldAssetsColours, graphFigSize, aggRes)
except KeyError: print("[FAILED] Household Weights Bar")

print(f"\n=== ALL OUTPUTS SAVED DIRECTLY TO: {graph_dir} ===")