import os
import pickle
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# =====================================================================
# 1. SETUP PATHS & LOAD BASELINE
# =====================================================================
project_dir = Path(os.getcwd())
data_dir = project_dir / "data"
graph_dir = data_dir / "graphs"
os.makedirs(graph_dir, exist_ok=True)

BASELINE_V_NUM = "baseline_debug27"
baseline_state_path = data_dir / f"Aggregated_State_{BASELINE_V_NUM}.pkl"

print(f"Loading baseline state from: {baseline_state_path}")
with open(baseline_state_path, "rb") as f:
    cached = pickle.load(f)

aggRes = cached["aggRes"]
assetResults = cached["assetResults"]
households = cached["households"]

if "time" in cached:
    time_hist = cached["time"]
else:
    import datetime as dt
    start = dt.datetime(2000, 1, 1)
    end = dt.datetime(2025, 1, 1)
    time_hist = pd.bdate_range(start=start, end=end).to_pydatetime().tolist()


graphFigSize = (14,6)
titleWeight = 'normal'
alpha = 0.2

householdDisplayLabels = {
    "0-20": "0–20th Income Percentile",
    "40-59": "40–59th Income Percentile",
    "80-100": "80–100th Income Percentile"
}

assetClassColours = {
    "Equities": "tab:red",
    "Bonds Short": "tab:blue",
    "Bonds Long": "tab:purple",
    "Property": "tab:orange",
    "Deposits": "tab:green",
    "Business Wealth": "#FFD700"
}

houseHoldAssetsColours = {
    "80-100": "tab:red",
    "0-20": "tab:blue",
    "40-59": "tab:green"
}

houseHoldAssetsColoursCumPaths = {
    "80-100": "crimson",
    "0-20": "mediumblue",
    "40-59": "green"
}

# =====================================================================
# 3. IMPORT AND EXECUTE  PLOTTING FUNCTIONS
# =====================================================================
from unseperated_main import (
    house_cum_sigma_banded_plot,
    householdVolatilityPlot,
    assetClassVolatilityBar
)

print("\nGenerating Cumulative Return Paths Graph...")
try:
    house_cum_sigma_banded_plot(
        assetRes=aggRes,
        time=time_hist,
        graphFigSize=graphFigSize,
        houseHoldAssetsColoursCumPaths=houseHoldAssetsColoursCumPaths,
        householdDisplayLabels=householdDisplayLabels,
        titleWeight=titleWeight,
        folder=str(graph_dir)
    )
    print("Success: cumRpaths.png")
except Exception as e:
    print(f"Failed: {e}")

print("\nGenerating Household Volatility Graph...")
try:
    householdVolatilityPlot(
        graphFigSize=graphFigSize,
        houseHoldAssetsColours=houseHoldAssetsColours,
        assetRes=aggRes,
        time=time_hist,
        folder=str(graph_dir)
    )
    print("Success: householdVolatility.png")
except Exception as e:
    print(f"Failed: {e}")

print("\nGenerating Asset Class Volatility Bar Chart...")
try:
    assetClassVolatilityBar(
        graphFigSize=graphFigSize,
        fullSavedAssetRes=assetResults,
        assetClassColours=assetClassColours,
        titleWeight=titleWeight,
        folder=str(graph_dir)
    )
    print("Success: assetClassVolBar.png")
except Exception as e:
    print(f"Failed: {e}")

print(f"\n=== ALL GRAPHS SAVED DIRECTLY TO: {graph_dir} ===")