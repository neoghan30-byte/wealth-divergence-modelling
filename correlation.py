
import pandas as pd
import numpy as np 
import unseperated_main as m
from pathlib import Path
import psutil
import os
import functools

def safe_load(file_path):
    try:
        import zstandard as zstd
        with zstd.open(file_path, "rb") as f:
            return pickle.load(f)
    except Exception:
        with open(file_path, "rb") as f:
            return pickle.load(f)

# coeffs_dict = 

SENSITIVITY_V_NUM = "sensitivityDebug27"
TARGET_PATHS = 5000

cfg = m.setup()
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

def diagnose(coeffs_dict):
    monthlyData = {}
    for assetClass in ['Property', 'Deposits']:
        if assetClass not in coeffs_dict:
            print(f"{assetClass!r} not in coeffs_dict at all")
            continue
        for ticker in coeffs_dict[assetClass]:
            cd = coeffs_dict[assetClass][ticker]
            raw = cd.get('histRetMonthly', cd.get('histRet', None))
            print(f"{assetClass} / {ticker}: raw is None = {raw is None}, "
                  f"type={type(raw)}, len={len(raw) if raw is not None else 'N/A'}")
            if raw is None:
                continue
            if isinstance(raw, pd.Series):
                s = raw.copy()
            else:
                s = pd.Series(np.asarray(raw).ravel())
            if not isinstance(s.index, pd.DatetimeIndex) or len(s.index) != len(s):
                s.index = pd.date_range(start=pd.Timestamp('2010-01-01'), periods=len(s), freq='MS')
            monthlyData[ticker] = s
            print(f"    -> assigned index: {s.index.min()} to {s.index.max()}, "
                  f"has NaN: {s.isna().sum()} / {len(s)}")
 
    print()
    print(f"monthlyData populated with {len(monthlyData)} tickers: {list(monthlyData.keys())}")
 
    if monthlyData:
        dfMonthly = pd.DataFrame(monthlyData)
        print(f"\ndfMonthly shape BEFORE dropna: {dfMonthly.shape}")
        print(f"NaN count per column:\n{dfMonthly.isna().sum()}")
        dfMonthly_clean = dfMonthly.dropna()
        print(f"\ndfMonthly shape AFTER dropna: {dfMonthly_clean.shape}")
        if len(dfMonthly_clean) < 2:
            print(">>> this is why monthlyTickers ENDS UP EMPTY (len < 2 after dropna) <<<")
    else:
        print(">>> monthlyData is EMPTY -- check why raw is None for Property/Deposits")
diagnose(old_coeffsDict) 
        