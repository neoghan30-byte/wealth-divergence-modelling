# -*- coding: utf-8 -*-
from pathlib import Path
import psutil
import os
import functools
import requests

if os.path.exists("/content/drive/MyDrive"):
    project_dir = Path("/content/drive/MyDrive/Young_Economist")
else:
    project_dir = Path(r"G:\My Drive\Young_Economist")
print(f"Hello WOrld")
use_GoogleDrive = False 
use_colab = False
# 2. DEFINE THE PATHS
if use_GoogleDrive:
    
    
    # data_dir = Path(r"G:\My Drive\Young_Economist")
    if os.path.exists("/content/drive/MyDrive"):
        project_dir = Path("/content/drive/MyDrive/Young_Economist")
        use_colab = True
    else:
        project_dir = Path(r"G:\My Drive\Young_Economist")
else:
    # Points to a local 'data' folder next to script
    project_dir = Path(__file__).parent 

# 3. 

data_dir = project_dir / "data"
chunk_dir = data_dir / "chunkResults"
graph_dir = data_dir / "graphs"
g_project_dir = Path(r"G:\My Drive\Young_Economist")

def get_data():
    """Downloads .pkl files from GitHub Releases if they aren't local."""
    
    has_pkl = list(chunk_dir.glob("*.pkl"))
    has_comparable = list(chunk_dir.glob("comparable*"))
    
    if not (has_pkl and has_comparable):
        print("Local data missing. Fetching from GitHub Release")
        
       
        api_url = "https://api.github.com/repos/neoghan30-byte/wealth-divergence-modelling/releases/tags/v1.0-data"
        
        try:
            response = requests.get(api_url)
            response.raise_for_status() # Check for 404 errors
            
            assets = response.json().get("assets", [])
            
            for asset in assets:
                name = asset["name"]
                download_url = asset["browser_download_url"]
                
                # filter
                if name.endswith(".pkl") or name.startswith("comparable"):
                    file_path = chunk_dir / name
                    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                    if not file_path.exists():
                        print(f"⬇Downloading {name}")
                        
                        # Download in chunks 
                        with requests.get(download_url, stream=True) as r:
                            r.raise_for_status()
                            with open(file_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                                    
            print("All required data downloaded successfully!")
            
        except requests.exceptions.HTTPError as e:
            print(f"\n ERROR: Could not connect to GitHub")
            print(f"Details: {e}")
            sys.exit(1)
    else:
        print("Required data found locally. Skipping download.")

get_data()
# print(os.path.exists(r"C:\Users\eogha\AppData\Local\Google"))

def validate_simulation(results):

    n = len(results["time"])

    for asset in results["assets"]:

        assert len(asset["returns"]) == n
        assert len(asset["wealth"]) == n

    return True
import logging
import traceback
import inspect
import logging
import traceback
import inspect
import os

# -----------------------------
# Ensure log directory exists
# -----------------------------
LOG_DIR = project_dir / "logs"
LOG_FILE = os.path.join(LOG_DIR, "pipeline_failures.log")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

# -----------------------------
# Configure logging 
# -----------------------------
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(message)s",
    force=True  # important if re-running in notebooks
)
def log_pipeline_failure(error=None, **kwargs):
    """
    Universal failure logger for simulation pipelines.

    Safe features:
    - works with Exception, string, or None
    - no dependency on external variables
    - auto-captures traceback if in except block
    - safe extraction of optional context
    - never crashes itself
    """

    # -----------------------------
    # Auto-context (optional)
    # -----------------------------
    frame = inspect.currentframe().f_back
    function_name = frame.f_code.co_name

    stage = kwargs.get("stage", function_name)
    V_num = kwargs.get("V_num", None)
    fname = kwargs.get("fname", None)
    chunkIndex = kwargs.get("chunkIndex", None)
    scenario = kwargs.get("scenario", None)
    hardCrash = kwargs.get("hardCrash", True)
    message = kwargs.get("message", None)
    # -----------------------------
    # Normalize error
    # -----------------------------
    if error is None:
        err_type = "UnknownError"
        err_msg = "No error provided"
        tb = None

    elif isinstance(error, Exception):
        err_type = type(error).__name__
        err_msg = repr(error)
        tb = traceback.format_exc()

    else:
        err_type = "ManualError"
        err_msg = str(error)
        tb = None
    
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

    # -----------------------------
    # Structured log
    # -----------------------------
    logging.error(
        "PIPELINE_FAILURE | "
        f"stage={stage} | "
        f"V_num={V_num} | "
        f"scenario={scenario} | "
        f"file={fname} | "
        f"chunkIndex={chunkIndex} | "
        f"error_type={err_type} | "
        f"error={err_msg}"
        f"message={message} | "
    )

    # traceback (if available)
    if tb:
        logging.error(tb)

    # -----------------------------
    # optional crash
    # -----------------------------
    if hardCrash and isinstance(error, Exception):
        raise error
# ________________________________________________________-
# analysis_from_chunks.py
#
# def testAnalysis(chunk_folder: str,
#     coeffs_dict: dict,
#     assets_completed: dict,
#     asset_weights: dict,
#     households: list,
#     time_hist: list,
#     convergence_checkpoints: list = None,
#     trading_days_per_year: int = 252,
#     backtest_pass_threshold: float = 0.85,
#     sim_low_pct: float = 5.0,
#     sim_high_pct: float = 95.0,
#     save_folder: str = None,
#     verbose: bool = True)
# ------------------------------------
#   from analysis_from_chunks import run_combined_analysis
#
#   results = run_combined_analysis(
#       chunk_folder    = "/content/drive/MyDrive/Young_Economist/chunkResults",
#       coeffs_dict     = coeffsDict,          # your fitted GARCH coefficients
#       assets_completed= assetsCompleted,
#       asset_weights   = assetWeights,
#       households      = households,
#       time_hist       = time,                # your full daily datetime list
#       convergence_checkpoints = [100, 500, 1000, 2000, 3000, 4000, 4999],
#       save_folder     = "/content/drive/MyDrive/Young_Economist/graphs",
#   )
#
#   # The dict returned contains:
#   #   results["convergence_df"]  — pd.DataFrame, one row per checkpoint
#   #   results["backtest_df"]     — pd.DataFrame, one row per household
#   #   results["backtest_raw"]    — dict with per-household sim/hist arrays
#
# IMPORTANT: the function expects chunk files named
#   Chunk_Results_<start>_<end>.pkl
# Each file must contain the key
# structure:
#   saved["chunkResults"]["monteCarlo"]["allHouseholdRet"]   list of path dicts
#   saved["chunkResults"]["monteCarlo"]["allHouseholdCum"]   list of path dicts
# =============================================================================

# What is needed:
#   1. Multiple bands (not just 5, 95)
#   2. Historical windows (i.e, 2008, 2016)
#   3. Stats tests ()

import zstandard as zstd
import os
import re
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from scipy.stats import probplot
import copy
import gc
import numbers
from icecream import ic
from scipy.stats import multivariate_t, t, norm


# #===================================================================
# Internal helpers
# #===================================================================
def get_absolute_max(obj):
    """Recursively finds the highest absolute numeric value in any structure."""
    import numpy as np
    import pandas as pd

    # 1. Base case: It's a single number
    if isinstance(obj, (int, float, np.number)):
        return abs(float(obj))
    
    # 2. It's a dictionary (e.g., your dictionary of paths)
    elif isinstance(obj, dict):
        return max((get_absolute_max(v) for v in obj.values()), default=0)
    
    # 3. It's a standard Python list, tuple, or set
    elif isinstance(obj, (list, tuple, set)):
        return max((get_absolute_max(v) for v in obj), default=0)
    
    # 4. It's a Pandas DataFrame or Series
    elif isinstance(obj, (pd.DataFrame, pd.Series)):
        return float(obj.abs().max().max() if isinstance(obj, pd.DataFrame) else obj.abs().max())
    
    # 5. It's a NumPy array
    elif isinstance(obj, np.ndarray):
        return float(np.max(np.abs(obj))) if obj.size > 0 else 0
        
    return 0
def find_value_location(obj, target_val, path=""):
    """
    Recursively digs through an object to find where a specific value lives.
    Returns a string tracking the path taken to get there.
    """
    import numpy as np
    import pandas as pd

    # 1. Base Case: It's a single number. Check if it matches our culprit.
    if isinstance(obj, (int, float, np.number)):
        if abs(float(obj)) == abs(target_val):
            return path
        return None

    # 2. If it's a dictionary (Tracks keys like ['path_42'])
    elif isinstance(obj, dict):
        for key, val in obj.items():
            loc = find_value_location(val, target_val, f"{path}['{key}']")
            if loc: return loc

    # 3. If it's a standard list or tuple (Tracks indices like [105])
    elif isinstance(obj, (list, tuple)):
        for idx, val in enumerate(obj):
            loc = find_value_location(val, target_val, f"{path}[Index {idx}]")
            if loc: return loc

    # 4. If it's a Pandas DataFrame (Tracks Row Label and Column Name)
    elif isinstance(obj, pd.DataFrame):
        # Find coordinates where value matches
        mask = (obj == target_val) | (obj == -target_val)
        rows, cols = np.where(mask)
        if len(rows) > 0:
            row_label = obj.index[rows[0]]
            col_name = obj.columns[cols[0]]
            return f"{path}[Row: {row_label}, Col: '{col_name}']"

    # 5. If it's a Pandas Series or NumPy Array
    elif isinstance(obj, (pd.Series, np.ndarray)):
        mask = (obj == target_val) | (obj == -target_val)
        indices = np.where(mask)[0]
        if len(indices) > 0:
            return f"{path}[Index/Row: {indices[0]}]"

    return None

def explode_test(maxAllowed, Object, file_location="Code Somewhere"):
      
      object_searched = Object
      maxFound = get_absolute_max(object_searched)
      location = find_value_location(object_searched, maxFound)
      assert maxFound < maxAllowed, (
      f"Error: returns have exploded. Max found {maxFound}, {location} in {file_location}"
      )
def _sorted_chunk_files(chunk_folder: str, V_num) -> list:
    """Return chunk filenames in ascending path-index order."""
    files = [
        f for f in os.listdir(chunk_folder)
        if re.match(rf"Chunk_Results_{V_num}_\d+_\d+\.pkl", f)
    ]
    filtered = []
    TARGET_PATHS = 5000
    for f in files:
        try:
            start_idx = int(f.replace(".pkl", "").split("_")[-2])
            if start_idx < TARGET_PATHS:
                filtered.append(f)
        except:
            pass
    return sorted(filtered, key=lambda f: int(re.search(r"_(\d+)_\d+\.pkl$", f).group(1)))



#===================================================================
# Back Tests / Validation
#===================================================================

def _asset_class_of(ticker, assets_completed):
    for asset_class, tickers in assets_completed.items():
        if ticker in tickers:
            return asset_class
    return None


def _build_hist_portfolio(
    coeffs_dict, assets_completed, asset_weights, households, time_hist,
    trading_days_per_year=252, verbose=False
) -> dict:
    """
    Re-create a daily historical portfolio return series for each household
    from the GARCH coefficient store (same data the simulation was fitted on).

    Returns
    -------
    dict: household -> pd.Series (daily returns, DatetimeIndex)
    """
    
    full_hist_index = pd.to_datetime(time_hist)

    # ---- Step 1: convert every asset's histRet / mu to a dated daily Series
    daily_series = {}
    for asset_class in assets_completed:
        for ticker in assets_completed[asset_class]:
            cd = coeffs_dict[asset_class][ticker]

            # raw = cd.get("histRet", cd.get("mu", None))
            raw = cd.get("histRetMonthly", cd.get("histRet", cd.get("mu", None)))
            if raw is None:
                if hardCrash:
                  raise KeyError(
                      f"No 'histRet' or 'mu' found for {ticker} ({asset_class}). "
                      f"Keys: {list(cd.keys())}"
                  )
                else:
                   
                  log_pipeline_failure(
                      KeyError(
                      f"No 'histRet' or 'mu' found for {ticker} ({asset_class}). "
                      f"Keys: {list(cd.keys())}"
                      ),
                      stage="build_hist",
                      raw_type=str(type(raw)),
                      # V_num=V_num,
                      # fname=fname,
                      
                  )
                  failed_count += 1 if 'failed_count' in locals() else 1

                  continue

            # Track whether this came from a monthly-cadence source (no real
            # DatetimeIndex attached) so we can assign dates at the correct
            # monthly frequency below, rather than assuming daily.
            was_monthly_source = isinstance(raw, (pd.Series, pd.DataFrame)) and not isinstance(
                (raw.index if isinstance(raw, (pd.Series, pd.DataFrame)) else None), pd.DatetimeIndex
            )

            # Normalise to pd.Series
            if isinstance(raw, pd.DataFrame):
                s = raw.iloc[:, 0].copy()
            elif isinstance(raw, np.ndarray):
                # Assign to the tail of the master index (convention from main script)
                s = pd.Series(raw.ravel(), index=full_hist_index[-len(raw):])
                was_monthly_source = False
            elif isinstance(raw, pd.Series):
                s = raw.copy()
            else:
                if hardCrash:
                    raise ValueError(
                        f"Unexpected type {type(raw)} for {ticker} histRet."
                    )
                else:
                    log_pipeline_failure(
                      ValueError(
                        f"Unexpected type {type(raw)} for {ticker} histRet."
                    ),
                      stage="build_hist",
                      # V_num=V_num,
                      # fname=fname,
                     
                  )
                    continue

            # Ensure DatetimeIndex
            if not isinstance(s.index, pd.DatetimeIndex):
               
                if was_monthly_source:
                    anchor = full_hist_index[-1].to_period("M").to_timestamp("M")
                    month_ends = pd.date_range(end=anchor, periods=len(s), freq="ME")
                    s.index = month_ends
                else:
                    s.index = full_hist_index[-len(s):]

            # Remove duplicate dates
            if not s.index.is_unique:
                s = s.groupby(s.index).mean()

            # Monthly data (< 500 obs) → resample to daily via ffill
            # if len(s) < 500:
            #     s = s.resample("D").ffill() / 21
            #     if verbose:
            #         print(f"  [{ticker}] monthly → resampled to daily, "
            #               f"length {len(s)}")
            # else:
            #     if verbose:
            #         print(f"  [{ticker}] daily, length {len(s)}, "
            #               f"mean {s.mean():.5f}")

            # daily_series[ticker] = s
            if len(s) < 500:
                s = s.resample("D").ffill() / 21
                print(f"  [{ticker}] monthly -> resampled to daily, "
                      f"length {len(s)}, index {s.index.min().date()} -> {s.index.max().date()}")
            else:
                print(f"  [{ticker}] daily, length {len(s)}, "
                      f"index {s.index.min().date()} -> {s.index.max().date()}, mean {s.mean():.5f}")

            # FIX: Convert log returns to simple returns before portfolio aggregation
            if globals().get('useLogs', True):
                s = np.exp(s) - 1.0

            daily_series[ticker] = s

    # ---- Step 2: per-household intersecting index -----------------
  
    hist_portfolio = {}
    household_common_index = {}
    for h in households:
        held_tickers = [
            ticker
            for asset_class in assets_completed
            for ticker in assets_completed[asset_class]
            if asset_weights[h][asset_class][ticker] != 0.0 and ticker in daily_series
        ]

        if not held_tickers:
            if verbose:
                print(f"  [{h}] WARNING: no tickers with nonzero weight found in daily_series")
            hist_portfolio[h] = pd.Series(dtype=float)
            household_common_index[h] = pd.DatetimeIndex([])
            continue

        df_h = pd.DataFrame({t: daily_series[t] for t in held_tickers})
        clean_h = df_h.dropna()
        common_index_h = clean_h.index
        household_common_index[h] = common_index_h

        if verbose or len(common_index_h) <= 5:
            print(f"  [{h}] held tickers: {held_tickers}")
            for t in held_tickers:
                ts = daily_series[t]
                print(f"      {t}: {len(ts)} obs, index {ts.index.min().date()} -> {ts.index.max().date()}, "
                      f"weight={asset_weights[h][_asset_class_of(t, assets_completed)][t]:.4f}")
            if len(common_index_h) > 0:
                print(f"  [{h}] Clean validation window: {common_index_h[0].date()} -> {common_index_h[-1].date()}")
                print(f"  [{h}] Total aligned trading days: {len(common_index_h)}")
            else:
                print(f"  [{h}] WARNING: dropna() left an EMPTY common index for tickers {held_tickers}")

        port = pd.Series(0.0, index=common_index_h)
        for asset_class in assets_completed:
            for ticker in assets_completed[asset_class]:
                w = asset_weights[h][asset_class][ticker]
                if w == 0.0:
                    continue
                port += w * clean_h[ticker]

        hist_portfolio[h] = port


    non_empty = [idx for idx in household_common_index.values() if len(idx) > 0]
    if len(non_empty) > 1:
        common_index = functools.reduce(lambda a, b: a.union(b), non_empty).sort_values()
    elif len(non_empty) == 1:
        common_index = non_empty[0]
    else:
        common_index = pd.DatetimeIndex([])

    return hist_portfolio, common_index


def _rolling_one_year(series_values: np.ndarray, window=252) -> np.ndarray:
    """Compound rolling 1-year returns from a daily return array."""
    n = len(series_values)
    if n < window:
        return np.array([np.prod(1 + series_values) - 1])
    out = np.empty(n - window + 1)
    for i in range(len(out)):
        out[i] = np.prod(1 + series_values[i: i + window]) - 1
    return out

def _make_table_pretty(df, name, folder, fontsize=13):
    """Render a DataFrame as a styled matplotlib table and save it."""
    # def smartRound(y, maxDec=4):
    #     x = y
    #     if pd.isnull(x):
    #       return ""
    #     if x == 0:
    #       return 0
    #     if isinstance(x, (int, np.integer)):
    #       return x
    #     return round(x, maxDec)
    def smartRound(y):
      if pd.isnull(y):
          return ""
      if isinstance(y, str):
          return y
      if y == 0:
          return "0.00"
      if isinstance(y, (int, np.integer)):
          return str(y)
      
    
      return f"{y * 100:.3f}"

    dfRound = df.copy()
    for col in dfRound.select_dtypes(include=[np.number]):


        # numCol = dfRound.select_dtypes(include=['float', 'int']).columns
        # dfRound[col] = dfRound[col].apply(smartRound)
        dfRound[col] = dfRound[col].map(smartRound)
    dfRound = dfRound.astype(object)
    fig_width = max(10, 2.5 * len(df.columns))
    fig_height = 1.0 + 0.55 * len(df)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")
    tbl = ax.table(cellText=dfRound.values, colLabels=df.columns,
                   cellLoc="center", loc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(fontsize)
    tbl.scale(1, 1.6)
    for j in range(len(df.columns)):
        tbl[(0, j)].set_facecolor("#2d4a6b")
        tbl[(0, j)].get_text().set_color("white")
        tbl[(0, j)].get_text().set_fontweight("bold")
    for i in range(len(df)):
        for j in range(len(df.columns)):
            tbl[(i + 1, j)].set_facecolor("#f5f5f5" if i % 2 == 0 else "white")
    plt.title(name, fontsize=14, fontweight="bold", pad=10)
    plt.tight_layout()
    savename = name.replace(" ", "_") + ".png"
    save_file_local = os.path.join(folder, savename)
    Path(folder).mkdir(parents=True, exist_ok=True)
    
    plt.savefig(save_file_local, dpi=300)
    backup_file(save_file_local)
    print("Save folder in convergence table", repr(save_file_local))
    plt.show()
    plt.close()
  
# def heatMap(histValues, simValues, households, bandDict):
#   pass
#   coverage_matrix = []
#   for h in households:
#     sim = simValues[h]
#     hist = histValues[h]
#     row = []
#     for expect_cov in bandDict:
#       low = (1 - expect_cov) / 2
#       high = 1 - low
def wealthGapDistribution(chunk_folder: str, households: list, V_num,
                           rich: str = "80-100", poor: str = "0-20",
                           mid: str = "40-59") -> dict:
    """
    Stream MC chunks and compute the distribution of the wealth gap
    (final cumulative return of `rich` minus final cumulative return of `poor`)
    across all simulated paths.

    Returns
    -------
    dict with keys:
        "gap_rich_poor"   : np.array of per-path gaps (rich - poor)
        "gap_rich_mid"    : np.array of per-path gaps (rich - mid)
        "gap_mid_poor"    : np.array of per-path gaps (mid - poor)
        "summary_df"      : pd.DataFrame with summary statistics
        "prob_positive"   : dict of P(gap > 0) for each pair
    """
    chunk_files = _sorted_chunk_files(chunk_folder, V_num)
    if not chunk_files:
        raise FileNotFoundError(f"No chunk files found in {chunk_folder}")

    gap_rich_poor = []
    gap_rich_mid  = []
    gap_mid_poor  = []

    for fname in chunk_files:
        fpath = os.path.join(chunk_folder, fname)


        try:
            try: 
                with zstd.open(fpath, "rb") as f:
                  saved = pickle.load(f)
            except zstd.ZstdError:
               with open(fpath, "rb") as f:
                saved = pickle.load(f)
        except Exception as e:
            log_pipeline_failure(
                  e,
                  stage="chunk_loading",
                  V_num=V_num,
                  fname=fname,
                  # chunkIndex=chunkIndex,
                  hardCrash=hardCrash
              )
              # continue
            print(f"Skipping corrupted chunk {fname}: {e}")
            continue
        # with open(fpath, "rb") as f:
        #     saved = pickle.load(f)
        cum_paths = saved["chunkResults"]["monteCarlo"]["allHouseholdCum"]

        for path in cum_paths:
            # Final cumulative return for each household in this path
            final = {h: path[h][-1] for h in [rich, poor, mid] if h in path}
            if len(final) < 3:
                continue
            gap_rich_poor.append(final[rich] - final[poor])
            gap_rich_mid.append(final[rich]  - final[mid])
            gap_mid_poor.append(final[mid]   - final[poor])

        del saved
        gc.collect()

    gap_rich_poor = np.array(gap_rich_poor)
    gap_rich_mid  = np.array(gap_rich_mid)
    gap_mid_poor  = np.array(gap_mid_poor)

    pairs = {
        f"{rich} vs {poor}": gap_rich_poor,
        f"{rich} vs {mid}":  gap_rich_mid,
        f"{mid} vs {poor}":  gap_mid_poor,
    }

    prob_positive = {k: (v > 0).mean() for k, v in pairs.items()}

    # ---- Summary table ----
    rows = []
    for label, gaps in pairs.items():
        rows.append({
            "Comparison":        label,
            "Median Gap":        f"{np.median(gaps):.1%}",
            "Mean Gap":          f"{np.nanmean(gaps):.1%}",
            "5th Pct":           f"{np.percentile(gaps, 5):.1%}",
            "95th Pct":          f"{np.percentile(gaps, 95):.1%}",
            "P(Gap > 0)":        f"{prob_positive[label]:.1%}",
            "N Paths":           len(gaps),
        })
    summary_df = pd.DataFrame(rows)
    return {
        "summary": summary_df,
        "raw": {
          "gap_rich_poor":  gap_rich_poor,
          "gap_rich_mid":   gap_rich_mid,
          "gap_mid_poor":   gap_mid_poor,
          "summary_df":     summary_df,
          "prob_positive":  prob_positive,
          "pairs": pairs},
        "core": {
           "object": pairs,
           "type": "?",
           "metrics": ["me", "med", "std", "p5", "p95"]
        }
    }



    # return {
    #     "gap_rich_poor":  gap_rich_poor,
    #     "gap_rich_mid":   gap_rich_mid,
    #     "gap_mid_poor":   gap_mid_poor,
    #     "summary_df":     summary_df,
    #     "prob_positive":  prob_positive,
    # }

# ---------------------------------------------------------------------------
# Table renderer
# ---------------------------------------------------------------------------

# def _render_backtest_table(df, save_folder=None, verbose=True):
#     fig, ax = plt.subplots(figsize=(14, 1.5 + 0.65 * len(df)))
#     ax.set_axis_off()
#     tbl = ax.table(
#         cellText=df.values, colLabels=df.columns,
#         cellLoc="center", loc="center"
#     )
#     tbl.auto_set_font_size(False)
#     tbl.set_fontsize(11)
#     tbl.scale(1, 1.8)

#     n_cols = len(df.columns)
#     for j in range(n_cols):
#         tbl[(0, j)].set_facecolor("#2d4a6b")
#         tbl[(0, j)].get_text().set_color("white")
#         tbl[(0, j)].get_text().set_fontweight("bold")

#     pass_col_idx = list(df.columns).index("Pass?")
#     for i, val in enumerate(df["Pass?"]):
#         row_color = "#c8f7c5" if val == "PASS" else "#f7c5c5"
#         tbl[(i + 1, pass_col_idx)].set_facecolor(row_color)
#         for j in range(n_cols):
#             if j != pass_col_idx:
#                 base = "#f5f5f5" if i % 2 == 0 else "white"
#                 tbl[(i + 1, j)].set_facecolor(base)

#     plt.title("Backtest Summary — Rolling 1-Year Return Coverage",
#               fontsize=12, fontweight="bold", pad=10)
#     plt.tight_layout()
#     if save_folder:
#         plt.savefig(os.path.join(save_folder, "backtest_table.png"), dpi=200)
#         if verbose:
#             print(f"  Saved backtest_table.png to {save_folder}")
#     plt.show()

def multiBandBacktest(sim_horizon: dict, hist_horizon: dict,
                      households: list, time_hist: list,
                      PERCENTILE_BANDS: dict, V_num: str, verbose: bool = False, chunk_folder: str = None, coeffs_dict: dict = None) -> dict:
    """
    Coverage test at four simultaneous probability bands.

    For a perfectly calibrated model, the "50% Band" should contain exactly
    50% of historical observations, the "80% Band" exactly 80%, etc.
    Systematic deviations reveal the direction of miscalibration.

    Returns
    -------
    dict:
        "coverage_df"   : pd.DataFrame — coverage % per household × band
        "heatmap_df"    : pd.DataFrame — same data formatted for display
        "sim_one_year"  : dict — per-household list of simulated 1Y returns
        "hist_one_year" : dict — per-household array of historical 1Y returns
    """
    # Build historical portfolio
    # if verbose:
    #     print("=== Multi-band backtest: building historical returns ===")
    # hist_portfolio, _ = _build_hist_portfolio(
    #     coeffs_dict, assets_completed, asset_weights, households, time_hist,
    #     verbose=verbose
    # )
    # hist_one_year = {
    #     h: _rolling_one_year(hist_portfolio[h].values, 252)
    #     for h in households
    # }

    # # Stream simulated 1-year returns from chunks
    # sim_one_year = {h: [] for h in households}
    # chunk_files  = _sorted_chunk_files(chunk_folder, V_num)
    # if not chunk_files:
    #     raise FileNotFoundError(f"No chunk files in {chunk_folder}")

    # for fname in chunk_files:
    #     fpath = os.path.join(chunk_folder, fname)
    #     try:
    #         try: 
    #             with zstd.open(fpath, "rb") as f:
    #               saved = pickle.load(f)
    #         except zstd.ZstdError:
    #            with open(fpath, "rb") as f:
    #             saved = pickle.load(f)
    #     except Exception as e:
    #         print(f"Skipping corrupted chunk {fname}: {e}")
    #         continue
    #     # with open(fpath, "rb") as f:
    #     #     saved = pickle.load(f)
    #     ret_paths = saved["chunkResults"]["monteCarlo"]["allHouseholdRet"]
    #     for path in ret_paths:
    #         for h in households:
    #             arr = path[h]
    #             one_yr = (np.prod(1 + arr[:252]) - 1) if len(arr) >= 252 \
    #                      else (np.prod(1 + arr) - 1)
    #             sim_one_year[h].append(one_yr)
    #     del saved
    #     gc.collect()

    # if verbose:
    #     for h in households:
    #         print(f"  [{h}] {len(sim_one_year[h])} simulated paths loaded")

    # Compute coverage at each band for each household
    coverage = {}   # household -> {band_name -> pct_covered}
    for h in households:
        coverage[h] = {}
        hist_vals = hist_horizon[h]
        sim_vals  = np.array(sim_horizon[h])
        for band_name, edges in PERCENTILE_BANDS.items():
            lo = np.percentile(sim_vals, edges["low"])
            hi = np.percentile(sim_vals, edges["high"])
            inside = ((hist_vals >= lo) & (hist_vals <= hi)).mean()
            coverage[h][band_name] = inside

    # ---- Coverage heatmap ----
    band_names = list(PERCENTILE_BANDS.keys())
    expected   = [0.50, 0.80, 0.90, 0.98]   # what perfect calibration gives

    # ---- Readable summary table ----
    rows = []
    for h in households:
        row = {"Household": h}
        for b, exp in zip(band_names, expected):
            actual = coverage[h][b]
            diff   = actual - exp
            sign   = "▲" if diff > 0 else "▼"
            row[b] = f"{actual:.0%} ({sign}{abs(diff):.0%})"
        rows.append(row)
    coverage_df = pd.DataFrame(rows)
    

    if verbose:
        print("\n=== Multi-band coverage (actual vs expected) ===")
        for h in households:
            parts = [f"{b}: {coverage[h][b]:.0%} (exp {e:.0%})"
                     for b, e in zip(band_names, expected)]
            print(f"  [{h}] " + " | ".join(parts))

    return {
        "summary": coverage_df,
        "raw": {
          "coverage_df":   coverage_df,
          "coverage_raw":  coverage,
          "sim_horizon":  sim_horizon,
          "hist_horizon": hist_horizon,
          "band_names": band_names,
          "expected": expected}
    }



def _crps_single(forecast_samples: np.ndarray, actual: float) -> float:
    """
    Continuous Ranked Probability Score for one observation.
   
    Lower is better. 0 = perfect deterministic forecast.
    """
    s = np.sort(forecast_samples)
    n = len(s)
    # E_F|X - y|: mean absolute deviation of forecast from observation
    term1 = np.nanmean(np.abs(s - actual))
    # 0.5 * E_F|X - X'|: spread of forecast (using the efficient formula)
    # = (1/n^2) * sum_i sum_j |s_i - s_j| / 2
    # Efficient O(n log n): after sorting, E|X-X'| = (2/n^2) sum_i s_i*(2i-n-1)
    ranks  = 2 * np.arange(1, n + 1) - n - 1
    term2  = np.dot(s, ranks) / (n * n)
    return term1 - term2


def crpsAnalysis(sim_horizon: dict, hist_horizon: dict,
                 households: list, time_hist: list,
                 V_num: str, n_hist_sample: int = 2000,
                 verbose: bool = True) -> dict: #chunk_folder: str, coeffs_dict: dict,
                #  assets_completed: dict, asset_weights: dict,
    """
    Compute the mean CRPS for each household's simulated 1-year return
    distribution against actual historical 1-year returns.

    A lower CRPS means the simulation is a better probabilistic forecast
    of reality for that household's portfolio.

    Parameters
    ----------
    n_hist_sample : int
        Number of historical windows to sample for speed. With 5000 sim paths
        and ~3500 historical windows, full evaluation is ~17.5M CRPS calls.
        Sampling 300 windows is representative and runs in seconds.

    Returns
    -------
    dict:
        "crps_scores"   : {household: mean CRPS}
        "crps_df"       : pd.DataFrame summary
        "sim_one_year"  : {household: np.array of simulated 1Y returns}
        "hist_one_year" : {household: np.array of historical 1Y returns}
    """
   

    # Compute CRPS for each household
    crps_scores     = {}
    crps_per_window = {}   # for the distribution plot

    # np.random.seed(42)   # reproducible sampling
    rng2 = np.random.default_rng(42)
    for h in households:
        sim_arr  = np.array(sim_horizon[h])
        hist_arr = hist_horizon[h]

        # Sample historical windows (or use all if fewer than n_hist_sample)
        if len(hist_arr) > n_hist_sample:
            sampled_idx  = rng2.choice(len(hist_arr), n_hist_sample,
                                            replace=False)
            sampled_hist = hist_arr[sampled_idx]
        else:
            sampled_hist = hist_arr

        scores = np.array([_crps_single(sim_arr, y) for y in sampled_hist])
        crps_scores[h]     = scores.mean()
        crps_per_window[h] = scores

        if verbose:
            print(f"  [{h}] Mean CRPS = {crps_scores[h]:.5f}  "
                  f"(n={len(sampled_hist)} historical windows, "
                  f"{len(sim_arr)} simulated paths)")
    # ---- Summary table ----
    rows = []
    for h in households:
        scores = crps_per_window[h]
        rows.append({
            "Household":   h,
            "Mean CRPS":   f"{crps_scores[h]:.5f}",
            "Median CRPS": f"{np.median(scores):.5f}",
            "Min CRPS":    f"{scores.min():.5f}",
            "Max CRPS":    f"{scores.max():.5f}",
            "N Windows":   len(scores),
        })
    crps_df = pd.DataFrame(rows)
    

    return {
        "summary": crps_df,
        "raw": {
          "crps_scores":    crps_scores,
          "crps_df":        crps_df,
          "crps_per_window": crps_per_window,
          "sim_one_year":   sim_horizon,
          "hist_one_year":  hist_horizon},
    }



# ---------------------------------------------------------------------------
# Back test entry point
# ---------------------------------------------------------------------------

def run_combined_analysis(
    chunk_folder: str,
    coeffs_dict: dict,
    assets_completed: dict,
    asset_weights: dict,
    households: list,
    time_hist: list,
    V_num: str,
    convergence_checkpoints: list = None,
    trading_days_per_year: int = 252,
    horizon_years: int = 5,
    backtest_pass_threshold: float = 0.85,
    sim_low_pct: float = 5.0,
    sim_high_pct: float = 95.0,
    verbose: bool = True,
) -> dict:
    """
    Single streaming pass: convergence + backtest from saved chunk files.

    Parameters
    ----------
    chunk_folder            : path to the directory containing Chunk_Results_*.pkl
    coeffs_dict             : your fitted GARCH coefficients dict
    assets_completed        : dict of {assetClass: set of ticker strings}
    asset_weights           : dict of {household: {assetClass: {ticker: weight}}}
    households              : e.g. ["80-100", "40-59", "0-20"]
    time_hist               : list of datetime objects (the full historical window)
    convergence_checkpoints : list of path-count integers at which to record
                              the running mean cumulative return.
                              Defaults to [100, 500, 1000, 2000, 3000, 5000].
    trading_days_per_year   : used for annualisation (default 252)
    backtest_pass_threshold : fraction of hist windows that must be inside
                              sim band to pass (default 0.85)
    sim_low_pct / sim_high_pct : percentile band edges (default 5 / 95)
    save_folder             : if given, saves PNG plots there
    verbose                 : print progress

    Returns
    -------
    dict with keys:
        "convergence_df"   pd.DataFrame — convergence table
        "convergence_raw"  list of rows, row = {path: x, h final cum: y for h in hs}
        "backtest_df"      pd.DataFrame — backtest summary table
        "backtest_raw"     dict         — per-household arrays for custom plots
    """

    if convergence_checkpoints is None:
        convergence_checkpoints = [100, 500, 1000, 2000, 3000, 5000]
    checkpoints = sorted(set(convergence_checkpoints))
    horizon_days = trading_days_per_year * horizon_years

    # ------------------------------------------------------------------
    # PREP: build historical portfolio return series (needed for backtest)
    # ------------------------------------------------------------------
    print(f"=== Building historical portfolio returns {horizon_years}-Year Horizon (verbose={verbose}) ===")
    hist_portfolio, _ = _build_hist_portfolio(
        coeffs_dict, assets_completed, asset_weights, households, time_hist,
        trading_days_per_year=trading_days_per_year, verbose=verbose
    )

    # Rolling 1-year windows from history (computed once, stored as arrays)
    hist_horizon = {
        h: _rolling_one_year(hist_portfolio[h].values, horizon_days)
        for h in households
    }
    if verbose:
        for h in households:
            print(f"  [{h}] {len(hist_horizon[h])} historical rolling windows. "
                  f"Mean: {np.nanmean(hist_horizon[h]):.2%}")

    # ------------------------------------------------------------------
    # STREAMING PASS
    # ------------------------------------------------------------------
    chunk_files = _sorted_chunk_files(chunk_folder, V_num)
    print(f"\n[DEBUG] TARGET FOLDER: {os.path.abspath(chunk_folder)}")
    print(f"[DEBUG] FOUND {len(chunk_files)}, in run_combined, MATCHING FILES: {chunk_files}\n")
    if not chunk_files:
        raise FileNotFoundError(f"No Chunk_Results_*.pkl files found in {chunk_folder}")
    if verbose:
        print(f"\n=== Streaming {len(chunk_files)} chunk files ===")
    
    # --- Welford online mean for convergence ---
    # mean_cum_final[h] = running mean of the FINAL value of each path's
    # cumulative return series (a scalar per path).
    
   
    TRACK_FULL_PATH = True   # set False to save RAM 

    welford_n    = 0                                  # total paths seen so far
    welford_mean = {h: None for h in households}      # running mean arrays
  
    sim_horizon = {h: [] for h in households}


    convergence_records = []
    checkpoints_done    = set()

    for fname in chunk_files:
        fpath = os.path.join(chunk_folder, fname)
        try:
          try: 
            with zstd.open(fpath, "rb") as f:
              saved = pickle.load(f)
          except zstd.ZstdError:
              with open(fpath, "rb") as f:
                saved = pickle.load(f)
          mc = saved["chunkResults"]["monteCarlo"]
        except Exception as e:
            log_pipeline_failure(
                  e,
                  stage="chunk_loading",
                  V_num=V_num,
                  fname=fname,
                  # chunkIndex=chunkIndex,
                  hardCrash=hardCrash
              )
            
            print(f"  WARNING: could not load {fname}: {e}")
            continue

        ret_paths = mc["allHouseholdRet"]   # list of {household: np.array}
        cum_paths = mc["allHouseholdCum"]   # list of {household: np.array}

        n_in_chunk = len(ret_paths)
        if verbose:
            print(f"  {fname}: {n_in_chunk} paths (total so far will be "
                  f"{welford_n + n_in_chunk})")

        for i in range(n_in_chunk):
            welford_n += 1
            ret_path = ret_paths[i]
            cum_path = cum_paths[i]

            for h in households:
                cum_arr = cum_path[h]   # shape (T,)

                # ---- Welford update ----
                if welford_mean[h] is None:
                    if TRACK_FULL_PATH:
                        welford_mean[h] = np.zeros_like(cum_arr, dtype=np.float64)
                    else:
                        welford_mean[h] = 0.0

                if TRACK_FULL_PATH:
                    delta = cum_arr - welford_mean[h]
                    welford_mean[h] += delta / welford_n
                else:
                    welford_mean[h] += (cum_arr[-1] - welford_mean[h]) / welford_n

                # ---- Backtest: n-year endpoint from this path ----
                ret_arr = ret_path[h]
                if len(ret_arr) >= horizon_days:
                    horizon_ret = np.prod(1 + ret_arr[:horizon_days]) - 1
                else:
                    horizon_ret = np.prod(1 + ret_arr) - 1
                sim_horizon[h].append(horizon_ret)

            # ---- Convergence checkpoint ----
            
            for cp in checkpoints:
                if cp not in checkpoints_done and welford_n >= cp:
                    record = {"Paths": welford_n}
                    for h in households:
                        if TRACK_FULL_PATH and welford_mean[h] is not None:
                            record[f"{h} Mean Final CumR"] = welford_mean[h][-1]
                        elif welford_mean[h] is not None:
                            record[f"{h} Mean Final CumR"] = welford_mean[h]
                        else:
                            record[f"{h} Mean Final CumR"] = np.nan
                    convergence_records.append(record)
                    checkpoints_done.add(cp)
                    if verbose:
                        vals = ", ".join(
                            f"{h}: {record[f'{h} Mean Final CumR']:.2%}"
                            for h in households
                        )
                        print(f"    Checkpoint {cp} paths: {vals}")

        del saved, mc, ret_paths, cum_paths
        import gc; gc.collect()

    # Record the final total as a last checkpoint
    final_record = {"Paths": welford_n}
    for h in households:
        if TRACK_FULL_PATH and welford_mean[h] is not None:
            final_record[f"{h} Mean Final CumR"] = welford_mean[h][-1]
        elif welford_mean[h] is not None:
            final_record[f"{h} Mean Final CumR"] = welford_mean[h]
        else:
            final_record[f"{h} Mean Final CumR"] = np.nan
    if welford_n not in checkpoints_done:
        convergence_records.append(final_record)

    if verbose:
        print(f"\n  Total paths streamed: {welford_n}")

    # ------------------------------------------------------------------
    # CONVERGENCE TABLE 
    # ------------------------------------------------------------------
    convergence_df = pd.DataFrame(convergence_records)

    return {
       "summary": convergence_df,
       "raw": {
        "convergence_df": convergence_df,
        "convergence_raw": convergence_records,
        "sim_horizon": sim_horizon,
        "hist_horizon": hist_horizon,
        "path_number": welford_n}
    }
def back_Test_pass_fail_results(households, hist_horizon, sim_horizon, backtest_pass_threshold, sim_low_pct, sim_high_pct, verbose=False):
    # ------------------------------------------------------------------
    # BACKTEST PASS/FAIL
    # ------------------------------------------------------------------
    if verbose:
        print("\n=== Backtest pass/fail ===")

    backtest_rows = []
    backtest_raw  = {}

    for h in households:
        hist_vals = hist_horizon[h]
        sim_vals  = np.array(sim_horizon[h])

        sim_lo = np.percentile(sim_vals, sim_low_pct)
        sim_hi = np.percentile(sim_vals, sim_high_pct)

        inside    = (hist_vals >= sim_lo) & (hist_vals <= sim_hi)
        pct_in    = inside.mean()
        passed    = pct_in >= backtest_pass_threshold

        backtest_raw[h] = {
            "hist_horizon": hist_vals,
            "sim_horizon":  sim_vals,
            "sim_lo":        sim_lo,
            "sim_hi":        sim_hi,
            "pct_within":    pct_in,
            "pass":          passed,
        }

        status = "PASS" if passed else "FAIL"
        if verbose:
            print(f"  [{h}] {pct_in:.1%} within sim [{sim_low_pct:.0f}th, "
                  f"{sim_high_pct:.0f}th] band  →  {status}  "
                  f"(threshold {backtest_pass_threshold:.0%})")

        backtest_rows.append({
            "Household":     h,
            "Hist Windows":  len(hist_vals),
            "Hist Mean 1Y":  f"{np.nanmean(hist_vals):.2%}",
            "Hist 5th pct":  f"{np.percentile(hist_vals, 5):.2%}",
            "Hist 95th pct": f"{np.percentile(hist_vals, 95):.2%}",
            "Sim 5th pct":   f"{sim_lo:.2%}",
            "Sim 95th pct":  f"{sim_hi:.2%}",
            "% Within Band": f"{pct_in:.1%}",
            "Pass?":         status,
        })

 
    household_order = {h: i for i, h in enumerate(households)}
    backtest_df = (
        pd.DataFrame(backtest_rows)
        .assign(_order=lambda d: d["Household"].map(household_order))
        .sort_values("_order")
        .drop(columns="_order")
        .reset_index(drop=True)
    )
    return {
        "raw": {
          "backtest_df": backtest_df,
          "backtest_raw": backtest_raw, 
          "sim_low_pct": sim_low_pct, 
          "sim_high_pct": sim_high_pct}
    }

def plot_monte_carlo_convergence(convergence_df, save_folder, households, pathNumber, verbose=False):
    fig, ax = plt.subplots(figsize=(12, 5))
    colours = {"80-100": "tab:red", "40-59": "tab:green", "0-20": "tab:blue"}
    for h in households:
        col = f"{h} Mean Final CumR"
        if col in convergence_df.columns:
            ax.plot(
                convergence_df["Paths"],
                convergence_df[col] * 100,
                marker="o", markersize=5,
                label=f"{h} percentile",
                color=colours.get(h, "grey")
            )
    ax.set_xlabel("Number of Monte Carlo Paths")
    ax.set_ylabel("Mean Final Cumulative Return (%)")
    ax.set_title("Monte Carlo Convergence — Mean Terminal Cumulative Return",
                 fontweight="bold")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(100.0))
    ax.legend(title="HH Income Group")
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    if save_folder:
        plt.savefig(os.path.join(save_folder, f"convergence_plot{pathNumber}.png"), dpi=200)
        if verbose:
            print(f"  Saved convergence_plot.png to {save_folder}")
    plt.show()


def backtest_distribution_plot(backtest_df, households, backtest_raw, sim_low_pct, sim_high_pct, path_number, save_folder, verbose=False):
    # ---- Backtest distribution plot ----
    fig, axes = plt.subplots(1, len(households),
                             figsize=(6 * len(households), 5), sharey=False)
    colours = {
    "80-100": "tab:red",
    "40-59": "tab:green",
    "0-20": "tab:blue"
    }
    if len(households) == 1:
        axes = [axes]

    try:
        import seaborn as sns
        has_sns = True
    except ImportError:
        has_sns = False

    for ax, h in zip(axes, households):
        c = colours.get(h, "grey")
        raw = backtest_raw[h]
        hist_v = raw.get("hist_one_year", raw.get("hist_horizon"))
        sim_v  = raw.get("sim_one_year", raw.get("sim_horizon"))

        if has_sns:
            sns.kdeplot(sim_v,  ax=ax, color=c, alpha=0.35, fill=True,
                        label="Simulated")
            sns.kdeplot(hist_v, ax=ax, color=c, linestyle="--", linewidth=2,
                        label="Historical")
        else:
            ax.hist(sim_v,  bins=60, color=c, alpha=0.3, density=True,
                    label="Simulated")
            ax.hist(hist_v, bins=30, color=c, alpha=0.7, density=True,
                    histtype="step", linewidth=2, label="Historical")

        ax.axvline(raw["sim_lo"], color=c, linestyle=":", linewidth=1.2)
        ax.axvline(raw["sim_hi"], color=c, linestyle=":", linewidth=1.2,
                   label=f"Sim {sim_low_pct:.0f}–{sim_high_pct:.0f}th pct")

        status = "PASS" if raw["pass"] else "FAIL"
        ax.set_title(f"Household {h}\n"
                     f"{raw['pct_within']:.1%} within band → {status}",
                     fontsize=12)
        ax.set_xlabel("1-Year Return")
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    fig.suptitle(
        "Backtest: Historical vs Simulated 1-Year Portfolio Returns",
        fontsize=14, fontweight="bold"
    )
    plt.tight_layout()
    if save_folder:
        plt.savefig(os.path.join(save_folder, f"backtest_distributions{path_number}.png"),
                    dpi=200)
        if verbose:
            print(f"  Saved backtest_distributions.png to {save_folder}")
    plt.show()

    
    # ---- Backtest table render ----
    _render_backtest_table(backtest_df, save_folder, verbose)

    
    # return {
    #     "convergence_df": convergence_df,
    #     "backtest_df":    backtest_df,
    #     "backtest_raw":   backtest_raw,
    # }


# ---------------------------------------------------------------------------
# Table renderer 
# ---------------------------------------------------------------------------

def _render_backtest_table(df, save_folder=None, verbose=False):
    fig, ax = plt.subplots(figsize=(14, 1.5 + 0.65 * len(df)))
    ax.set_axis_off()
    tbl = ax.table(
        cellText=df.values, colLabels=df.columns,
        cellLoc="center", loc="center"
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)
    tbl.scale(1, 1.8)

    n_cols = len(df.columns)
    for j in range(n_cols):
        tbl[(0, j)].set_facecolor("#2d4a6b")
        tbl[(0, j)].get_text().set_color("white")
        tbl[(0, j)].get_text().set_fontweight("bold")

    pass_col_idx = list(df.columns).index("Pass?")
    for i, val in enumerate(df["Pass?"]):
        row_color = "#c8f7c5" if val == "PASS" else "#f7c5c5"
        tbl[(i + 1, pass_col_idx)].set_facecolor(row_color)
        for j in range(n_cols):
            if j != pass_col_idx:
                base = "#f5f5f5" if i % 2 == 0 else "white"
                tbl[(i + 1, j)].set_facecolor(base)

    plt.title("Backtest Summary — Rolling 1-Year Return Coverage",
              fontsize=12, fontweight="bold", pad=10)
    plt.tight_layout()
    if save_folder:
        plt.savefig(os.path.join(save_folder, "backtest_table.png"), dpi=200)
        if verbose:
            print(f"  Saved backtest_table.png to {save_folder}")
    plt.show()
from scipy.integrate import quad

def crps(forecast_samples, actual):
    """
    Continuous Ranked Probability Score
    Lower is better. Perfect forecast = 0.
    """
    forecast_samples = np.array(forecast_samples)
    actual = float(actual)

    # Empirical CDF of forecast
    sorted_forecast = np.sort(forecast_samples)
    cdf_forecast = np.arange(1, len(sorted_forecast) + 1) / len(sorted_forecast)

    # Integrate (F(y) - 1{y >= actual})^2 dy
    crps_value = 0
    prev_y = sorted_forecast[0]
    prev_f = 0

    for y, f in zip(sorted_forecast, cdf_forecast):
        indicator = 1 if prev_y >= actual else 0
        crps_value += (prev_f - indicator) ** 2 * (y - prev_y)
        prev_y = y
        prev_f = f

    # Tail after last observation
    indicator = 1 if prev_y >= actual else 0
    crps_value += (1 - indicator) ** 2 * (prev_y - actual) if prev_y < actual else 0

    return crps_value

# Compare across households
# for h in households:
#     crps_scores = []
#     for hist_return in historical_returns[h][:100]:  # Sample for speed
#         crps_scores.append(crps(simulated_returns[h], hist_return))
#     print(f"{h}: Mean CRPS = {np.nanmean(crps_scores):.4f}")


#===================================================================
# Graphing / Analysis
#===================================================================
def CRPS_bar_chart(crps_scores, crps_per_window, folder):
    # ---- Bar chart of mean CRPS per household ----
    colours = {"80-100": "tab:red", "40-59": "tab:green", "0-20": "tab:blue"}
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: mean CRPS bar chart
    ax = axes[0]
    hs    = list(crps_scores.keys())
    vals  = [crps_scores[h] for h in hs]
    cols  = [colours.get(h, "grey") for h in hs]
    bars  = ax.bar(hs, [v * 100 for v in vals], color=cols, edgecolor="black",
                   linewidth=0.8, alpha=0.8)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.001 * 100,
                f"{v:.4f}", ha="center", va="bottom", fontsize=11)
    ax.set_ylabel("Mean CRPS (×100)")
    ax.set_title("Mean CRPS per Household\n(lower = better calibrated)", fontsize=12)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Right: box plot of CRPS distribution across historical windows
    ax2 = axes[1]
    data   = [crps_per_window[h] * 100 for h in hs]
    bp     = ax2.boxplot(data, patch_artist=True, notch=False)
    for patch, col in zip(bp["boxes"], cols):
        patch.set_facecolor(col)
        patch.set_alpha(0.6)
    ax2.set_ylabel("CRPS per historical window (×100)")
    ax2.set_title("CRPS Distribution Across\nHistorical Windows", fontsize=12)
    ax2.grid(axis="y", linestyle="--", alpha=0.4)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.suptitle(
        "Continuous Ranked Probability Score (CRPS)\n"
        "Simulated 5-Year Return Distribution vs Historical Observations",
        fontsize=14, fontweight="bold"
    )
    plt.tight_layout()
    plt.savefig(os.path.join(folder, "crps_analysis.png"), dpi=300)
    plt.show()
    plt.close()



def houseCumSampleWithSigmaBanded(assetRes, time, households, makeTable=False):
    sample_path_length = assetRes['portSampleCum'][households[0]][0].shape[0]
    x = pd.to_datetime(time)[:sample_path_length] # Slices x to exactly 913 (or whatever path size is)

    
    sampleSummaryRows = []
    plottingList = {}

    for h in households:
      plottingList[h] = []
      for path in assetRes['portSampleCum'][h]:
        plottingList[h].append(path[-1])
      sampleSummaryRows.append({
          "Household": h,
          "Std of Paths Cumulative Return": np.nanstd(plottingList[h]),
          "Maximum Return": max(plottingList[h]),
          "Minimum Return": min(plottingList[h])
      })

    sampleSummary = pd.DataFrame(sampleSummaryRows)
    # if makeTable:
      #  makeTablePretty(sampleSummary, 'Household Cumulative Returns With Volatility Bands', 
    return {
       "summary": sampleSummary,
       "raw": {"plottingList": plottingList, "house_cum_df": sampleSummary},
    }

def assetClassVolatility(fullSavedAssetRes):
    sigmaList = []
    colourList = []
    labelList = []
    for assetClass in fullSavedAssetRes['sigmaAssetClassPath']:
      sigmaList.append(np.nanmean(fullSavedAssetRes['sigmaAssetClassPath'][assetClass]))
      labelList.append(f"{assetClass}")
    return {
       "raw": {
        "labelList": labelList,
        "sigmaList": sigmaList,
       }
    }
# sigmaList, labelList
def getHouseholdVolTable(aggRes, households): 
  meanLists = {h: [] for h in households}
  stdLists = {h: [] for h in households}
  p5_lists = {h: [] for h in households}
  p95_lists = {h: [] for h in households}
  sigma_list = {h: [] for h in households}
  houseVolatilityRows = []
  meanPath = {}
  pathStd = {}
  for h in households:
    
   
    sigma = aggRes['portSampleSigma'][h]
    # p95_lists[h] =
    for path in sigma:
       
       assert len(path) > 500, "Nominal path in getHouseholdVolAnalysis is not a path"
       meanLists[h].append(np.nanmean(path))
       stdLists[h].append(np.nanstd(path))
       p5_lists[h].append(np.nanpercentile(path, 5))
       p95_lists[h].append(np.nanpercentile(path, 95))
       sigma_list[h].append(path)
       if globals().get("sigma_list_debug", False):
          ic(
            h,
            type(sigma_list[h]),
            len(sigma_list[h])
          )
          if len(sigma_list[h]) > 0:
            ic(
                np.shape(sigma_list[h][0])
            )
    single_sigma_path = aggRes['portSigma'][h]
    houseVolatilityRows.append({
            "Household": h,
            # "Final Volatility": sigma[-1],
            "(Mean Path) Mean Volatility": np.nanmean(single_sigma_path),
            "(Mean Path) Std of Volatility": np.nanstd(single_sigma_path),
            "Std of Path Mean Volatilities": np.nanstd(meanLists[h]),
        })
    meanPath[h] = np.nanmean(sigma_list[h], axis=0)
    pathStd[h] = np.nanstd(sigma_list[h], axis=0) #np.nanstd(sigma_list[h])
  houseVolTable = pd.DataFrame(houseVolatilityRows)
  # Preserve caller-supplied household order (income order) rather than
  # alphabetically reordering -- alphabetical sort flips display order
  # relative to every chart legend / colour map in the pipeline.
  household_order = {h: i for i, h in enumerate(households)}
  houseVolTable = (
      houseVolTable
      .assign(_order=houseVolTable["Household"].map(household_order))
      .sort_values("_order")
      .drop(columns="_order")
      .reset_index(drop=True)
  )
  return { # work in progress
     "summary": houseVolTable,
     "raw": {
        "house_vol_df": houseVolTable,
        "meanPath": meanPath,
        "pathStd": pathStd,
        "meanLists": meanLists,
        "stdLists": stdLists,

     },
     "core": {
        "series": {
          #  "values": sigmaDict,
           "name": "Household Volatility Series",
           "index": households
        }
     }
  }


      
       
# def getHouseholdVolTable(aggRes, households, makeTable=False):
#   houseVolatilityRows = []
#   sigmaDict = {}
#   for h in households:
#     sigma = aggRes['portSigma'][h]
#     houseVolatilityRows.append({
#             "Household": h,
#             "Final Volatility": sigma[-1],
#             "Mean Volatility": np.nanmean(sigma),
#             "Std of Volatility": np.nanstd(sigma)
#         })
#     sigmaDict[h] = sigma
#   houseVolTable = pd.DataFrame(houseVolatilityRows)
#   #sort
#   houseVolTable = houseVolTable.sort_values(by=["Household"]).reset_index(drop=True)
#   return {
#      "raw": {"house_vol_df": houseVolTable},
#      "core": {
#         "series": {
#            "values": sigmaDict,
#            "name": "Household Volatility Series",
#            "index": households
#         }
#      }

#   }
  # if makeTable:
    # print("\n=== Household Volatility Summary ===")
    # # print(houseVolTable)
    # makeTablePretty(houseVolTable, 'Household Volatility Summary', folder)
# getHouseholdVolTable()


def getAssetVolTable(fullSavedAssetRes, makeTable=False):
  assetVolatilityRows = []
  sigmaDict = {}
  assetClasses = []
  for assetClass in fullSavedAssetRes['sigmaAssetClassPath']:
      sigma = fullSavedAssetRes['sigmaAssetClassPath'][assetClass]
      assetVolatilityRows.append({
          "Asset Class": assetClass,
          "Final Volatility": sigma[-1],
          "Mean Volatility": np.nanmean(sigma),
          "Std of Volatility": np.nanstd(sigma)
        })
      sigmaDict[assetClass] = sigma
      assetClasses.append(assetClass)

  assetVolTable = pd.DataFrame(assetVolatilityRows)
  #sort
  assetVolTable = assetVolTable.sort_values(by=["Asset Class"]).reset_index(drop=True)
  assetVolTableCore = copy.deepcopy(assetVolTable)
  return {
     "raw": {"assetVol_df": assetVolTable,
             "sigma_dict": sigmaDict},
     "core": {
        "series": {
           "values": sigmaDict,
           "name": "Asset Class Volatility Series",
           "index": assetClasses
        }
     }

    #  "core": assetVolTableCore.drop(columns="Final Volatility", errors='ignore').drop(index="Final Volatility", errors='ignore')
  }
  # if makeTable:
    # print("\n=== Asset Class Volatility Summary ===")
    # makeTablePretty(assetVolTable, 'Asset Class Volatility Summary', folder)
# getAssetVolTable()


def meanHousePath(aggRes, households):
  meanSummaryRows = []
  seriesValues = {}
  finalVals = {h: 0 for h in households}
  for h in households:
    meanPath = aggRes['portCumR'][h]
    print(f"{h} {aggRes['portCumR'][h].shape}")
    finalVals[h] = aggRes['portCumR'][h][-1]
    seriesValues[h] = meanPath
    meanSummaryRows.append({
          "Household": h,
          "Final Return": finalVals[h],
          # "Std of Paths Cumulative Return": np.nanstd(finalVals[h]),
          # "Maximum Return": ,
          # "Minimum Return": min(plottingList[h])
      })
  meanSummary = pd.DataFrame(meanSummaryRows)
  # if makeTable:
  #   makeTablePretty(meanSummary, 'Mean Path Final Returns', folder)
  return {
      "meanSummary_df": meanSummary,
      "raw": {"meanPath": seriesValues, "meanSummary_df": meanSummary},
      "core": {
         "series": {
             "values": seriesValues,
             "name": "Mean_Path",
             "index": households,
         },
         "terminal": {
             "values": finalVals,
             "name": "Terminal Cumulative Return",
             "index": households,

         }, 
      }
  }


def get_presentingAssetReturns(asset_level_res, households, assets, time):
    """
    Extracts and aggregates the historical mean cumulative return paths 
    for each broad asset class expected by the downstream metric analysis.
    """
    #asset_level_res = aggRes, not actually asset_level
    presentingAssetReturns = {}
    mean_asset_paths = asset_level_res.get('meanAssetPath', {})
    portAssetRet = asset_level_res.get('portAssetRet', {})

    for h in households:
        fallback_len = len(time)
        for ac_dict in portAssetRet[h].values():
            if isinstance(ac_dict, dict) and ac_dict:
                fallback_len = len(next(iter(ac_dict.values())))
                break
        presentingAssetReturns[h] = {}
        if h not in portAssetRet:
           continue
        for assetClass in assets:
            class_daily_ret = None
            if assetClass in portAssetRet[h]:
               for ticker, weighted_ret_array in portAssetRet[h][assetClass].items():
                    if class_daily_ret is None:
                        class_daily_ret = np.zeros_like(weighted_ret_array)
                    class_daily_ret += weighted_ret_array
            if class_daily_ret is not None:
                # Convert the summed daily weighted returns into a cumulative return path
                class_cum_ret = np.cumprod(1 + class_daily_ret) - 1.0
                presentingAssetReturns[h][assetClass] = class_cum_ret
                # data = mean_asset_paths[assetClass]
                
                # if isinstance(data, dict):
                #     # If it's a nested dictionary of individual tickers, sum their arrays up
                #     assetClassSeries = None
                #     for tickerName, path_array in data.items():
                #         if assetClassSeries is None:
                #             assetClassSeries = np.zeros_like(path_array)
                #         assetClassSeries += path_array
                #     presentingAssetReturns[h][assetClass] = assetClassSeries
                # else:
                #     # If it's already a pre-aggregated flat NumPy array
                #     presentingAssetReturns[h][assetClass] = data
            else:
                # Fallback to a zero array if the asset class wasn't simulated/found
                # Dynamically find length from another asset to avoid hardcoding or NameErrors
                print(f"notice_me!!!!!!!!!!!!!!!!!!!!!/n presenting asset returns is falling back to zeros.")
                fallback_len = len(time)
                # for any_asset in mean_asset_paths.values():
                #     if isinstance(any_asset, dict) and any_asset:
                #         fallback_len = len(next(iter(any_asset.values())))
                #         break
                #     elif isinstance(any_asset, np.ndarray):
                #         fallback_len = len(any_asset)
                #         break
                # presentingAssetReturns[h][assetClass] = np.zeros(fallback_len)
                

    return presentingAssetReturns

def geometric_contributions_from_presenting(presentingAssetReturns, household):


    assets_dict = presentingAssetReturns[household]



    asset_period = {}
    for a, cum_series in assets_dict.items():


        gross = 1 + cum_series
        r = gross[1:] / gross[:-1] - 1
        r = np.insert(r, 0, gross[0] - 1)


        asset_period[a] = r


    #  Portfolio return path
    rp = np.sum(list(asset_period.values()), axis=0)
    gross_p = 1 + rp


    # Forward compounding factors
    forward_growth = np.flip(np.cumprod(np.flip(gross_p)))


    # Geometric contributions
    contributions = {}
    for a in asset_period:
        contributions[a] = np.sum(asset_period[a] * forward_growth)


    final_wealth = np.prod(gross_p)


    return contributions, final_wealth


def get_gap_geometric(presentingAssetReturns):
    # return {
    #     "summary_df": gap_summary_df,
    #     "raw": {
    #       "order": order,
    #       "gaps": gaps,
    #       "labels": labels,
    #       "rich_vals": rich_vals,
    #       "poor_vals": poor_vals,
    #       },

    rich = "80-100"
    poor = "0-20"


    rich_contrib, rich_W = geometric_contributions_from_presenting(
        presentingAssetReturns, rich
    )


    poor_contrib, poor_W = geometric_contributions_from_presenting(
        presentingAssetReturns, poor
    )


    asset_categories = list(rich_contrib.keys())


    gaps = []
    labels = []
    rich_vals = []
    poor_vals = []


    for cat in asset_categories:


        rich_pct = rich_contrib[cat] * 100
        poor_pct = poor_contrib[cat] * 100


        gap = rich_pct - poor_pct


        gaps.append(gap)
        labels.append(cat)
        rich_vals.append(rich_pct)
        poor_vals.append(poor_pct)


    gaps = np.array(gaps)


    order = np.argsort(np.abs(gaps))[::-1]
    gaps = gaps[order]
    labels = np.array(labels)[order]
    rich_vals = np.array(rich_vals)[order]
    poor_vals = np.array(poor_vals)[order]
    gap_summary_df = pd.DataFrame({
        "pair": labels,
        "order": order,
        "wealth_gap": gaps,
        "rich_terminal_wealth": rich_vals,
        "poor_terminal_wealth": poor_vals,
    })

    gap_summary_df = gap_summary_df.sort_values(
        "wealth_gap",
        ascending=False
    ).reset_index(drop=True)
    return {
        "summary_df": gap_summary_df,
        "raw": {
          "order": order,
          "gaps": gaps,
          "labels": labels,
          "rich_vals": rich_vals,
          "poor_vals": poor_vals,
          "summary_df": gap_summary_df,
          },
        
        # "meta"
        
}

def get_metric_analysis(
    chunk_folder: str,
    coeffs_dict: dict,
    assets_completed: dict,
    asset_weights: dict,
    households: list,
    time_hist: list,
    V_num: str,
    percentile_bands: dict,
    aggRes: dict,
    asset_level_res: dict,
    convergence_checkpoints: list = None,
    trading_days_per_year: int = 252,
    backtest_pass_threshold: float = 0.85,
    sim_low_pct: float = 5.0,
    sim_high_pct: float = 95.0,
    save_folder: str = None,
    horizon_years: str = 1,
    debugMetrics: bool = False, 
    ):
  
      #households, coeffs_dict, assets_completed, asset_weights, time_hist, save_folder, percentile_bands):
  convergence_results = run_combined_analysis(
      chunk_folder = chunk_folder,
      coeffs_dict = coeffs_dict,
      assets_completed = assets_completed,
      asset_weights = asset_weights,
      households = households,
      time_hist = time_hist,
      V_num = V_num,
      horizon_years= horizon_years
  )
  hist_horizon = convergence_results["raw"].get("hist_horizon")
  sim_horizon = convergence_results["raw"].get("sim_horizon")

  #===== calling other back tests
  gap_results = wealthGapDistribution(
        chunk_folder = chunk_folder,
        households = households,
        V_num = V_num,
        # verbose=debugMetrics
  )
  
  band_results = multiBandBacktest(
      sim_horizon = sim_horizon,
      hist_horizon = hist_horizon,
      households = households,
      time_hist = time_hist,
      PERCENTILE_BANDS = percentile_bands,
      V_num = V_num,
      verbose=debugMetrics
  )
  crps_results = crpsAnalysis(
      sim_horizon = sim_horizon,
      hist_horizon = hist_horizon,
      households = households,
      time_hist = time_hist,
      V_num = V_num,
      verbose=debugMetrics
  )

 
  mean_household_results = meanHousePath(aggRes, households)
  asset_vol_results = getAssetVolTable(asset_level_res)
  house_cum_results = houseCumSampleWithSigmaBanded(aggRes, time_hist, households)
  house_vol_results = getHouseholdVolTable(aggRes, households)
  asset_class_vol_results = assetClassVolatility(asset_level_res) #Not a DF, two lists
  back_test_results = back_Test_pass_fail_results(households, hist_horizon, sim_horizon, 
                                                  backtest_pass_threshold=backtest_pass_threshold, sim_low_pct=sim_low_pct, 
                                                  sim_high_pct=sim_high_pct, verbose=debugMetrics)

  presentingAssetReturns = get_presentingAssetReturns(aggRes, households, assets_completed, time_hist)
  gap_geometric_results = get_gap_geometric(presentingAssetReturns)
  return {
    "validation": {
      "band_results": band_results,
      "crps_results": crps_results,
      "convergence_results": convergence_results,
      "back_test_results": back_test_results,

    },
    "results": {
      "gap_results": gap_results,
      "mean_household_results": mean_household_results,
      "asset_vol_results": asset_vol_results,
      "house_cum_results": house_cum_results,
      "house_vol_results": house_vol_results,
      # "asset_class_results": asset_class_results,
      "presentingAssetReturns": presentingAssetReturns,
      "gap_geometric_results": gap_geometric_results,
    },
    "inputs": {
       "assetWeights": asset_weights,
       "assets": assets_completed,
    }
  }



#=========================================================
# Graphing
#========================================================
def getHeatMap(households, coverage_df, coverage, sim_one_year, hist_one_year, band_names, expected, folder, horizon_years=1):
    fig, ax = plt.subplots(figsize=(10, 4 + 0.6 * len(households)))

    matrix     = np.array([[coverage[h][b] for b in band_names] for h in households])
    expected_r = np.array(expected)

    # Colour by deviation from expected: green = over-coverage, red = under
    deviation  = matrix - expected_r[np.newaxis, :]

    im = ax.imshow(deviation, cmap="RdYlGn", vmin=-0.3, vmax=0.3, aspect="auto")
    plt.colorbar(im, ax=ax, label="Coverage − Expected")

    ax.set_xticks(range(len(band_names)))
    ax.set_xticklabels(
        [f"{b}\n(expected {e:.0%})" for b, e in zip(band_names, expected)],
        fontsize=11
    )
    ax.set_yticks(range(len(households)))
    ax.set_yticklabels(households, fontsize=11)

    # Annotate each cell with actual coverage %
    for i, h in enumerate(households):
        for j, b in enumerate(band_names):
            actual = coverage[h][b]
            colour = "black" if abs(deviation[i, j]) < 0.15 else "white"
            ax.text(j, i, f"{actual:.0%}", ha="center", va="center",
                    fontsize=12, fontweight="bold", color=colour)

    ax.set_title(
        "Backtest Calibration Heatmap\n"
        f"Coverage of historical {horizon_years}-year returns inside simulated bands\n"
        "(Green = over-coverage, Red = under-coverage vs expected)",
        fontsize=13, fontweight="bold"
    )
    plt.tight_layout()
    plt.savefig(os.path.join(folder, "multiband_backtest_heatmap.png"), dpi=300)
    plt.show()
    plt.close()

def plot_wealth_gap_dist(pairs, summary_df, prob_positive, folder, rich="80-100", mid="40-59", poor="0-20"):
    _make_table_pretty(summary_df, "Wealth Gap Summary", folder)

    # ---- Main plot: distribution of rich-poor gap ----
    colours = {
        f"{rich} vs {poor}": "tab:red",
        f"{rich} vs {mid}":  "tab:orange",
        f"{mid} vs {poor}":  "tab:blue",
    }

    fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=False)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 13})

    for ax, (label, gaps) in zip(axes, pairs.items()):
        c = colours[label]
        # Histogram
        ax.hist(gaps * 100, bins=60, color=c, alpha=0.55, density=True, edgecolor="none")

        # Vertical lines: median and 90% CI
        median = np.median(gaps) * 100
        p5     = np.percentile(gaps, 5) * 100
        p95    = np.percentile(gaps, 95) * 100

        ax.axvline(median, color=c, linewidth=2.0, label=f"Median: {median:.1f}%")
        ax.axvline(p5,  color=c, linewidth=1.2, linestyle="--",
                   label=f"5th–95th pct: [{p5:.1f}%, {p95:.1f}%]")
        ax.axvline(p95, color=c, linewidth=1.2, linestyle="--")
        ax.axvline(0,   color="black", linewidth=1.0, linestyle=":")

        # Shade region where gap < 0 (lower household outperforms)
        x_fill = np.linspace(gaps.min() * 100, 0, 200)
        ax.fill_betweenx([0, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 1],
                          gaps.min() * 100, 0,
                          color="grey", alpha=0.12, label=f"P(gap≤0): {1-prob_positive[label]:.1%}")

        p_pos = prob_positive[label]
        ax.set_title(f"{label}\nP(gap > 0) = {p_pos:.1%}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Final Cumulative Return Gap (%)")
        ax.set_ylabel("Density")
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(100.0))
        ax.legend(fontsize=9)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.suptitle(
        "Distribution of Wealth Gap Across 25-Year Simulated Horizons\n"
        "(Positive = higher-income household outperforms)",
        fontsize=15, fontweight="bold"
    )
    plt.tight_layout()
    plt.savefig(os.path.join(folder, "wealth_gap_distribution.png"), dpi=300)
    plt.show()
    plt.close()

    print("\n=== Wealth Gap Summary ===")
    for label, p in prob_positive.items():
        print(f"  {label}: P(gap > 0) = {p:.1%}, "
              f"median gap = {np.median(pairs[label]):.1%}")
# -------------------------------
# results analysis
# -------------------------------

def makeTablePretty(df, name, folder, fontsize=16, col_width=4, row_height=1, header_color='darkslategray', row_colors=['lightgray', 'w'], edge_color='w'):

  # def smartRound(y, maxDec=7):
  #   x = y
  #   if pd.isnull(x):
  #     return ""
  #   if x == 0:
  #     return 0
  #   mag = -int(np.floor(np.log10(abs(x))))
  #   decimals = max(0, min(mag, maxDec))
  #   fractionRes = round(x, decimals + 2)
  #   result = fractionRes * 100
  #   return result
  def smartRound(y):
    if pd.isnull(y):
        return ""
    if y == 0:
        return "0.00"
    if isinstance(y, (int, np.integer)):
        return str(y)
    
  
    return f"{y * 100:.4f}"

  dfRound = df.copy()
  for col in dfRound.select_dtypes(include=[np.number]):


    # numCol = dfRound.select_dtypes(include=['float', 'int']).columns
    dfRound[col] = dfRound[col].apply(smartRound)
  df = dfRound
  fig_width = col_width * len(df.columns)
  fig_height = row_height * (len(df)) + 1


  fig, ax = plt.subplots(figsize=(fig_width, fig_height))
  ax.axis('off')


  mpl_table = ax.table(
      cellText=df.values,
      colLabels=df.columns,
      cellLoc='center',
      loc='center'
  )
  mpl_table.scale(1, 1.5)
  plt.tight_layout(pad=0)
  # plt.subplots_adjust(top=1, bottom=0, left=0, right=1)
  plt.subplots_adjust(top=0.88, bottom=0.05)
  ax.set_position([0, 0, 1, 1])
  mpl_table.auto_set_font_size(False)
  mpl_table.set_fontsize(fontsize)


  # Color header
  for (i, j), cell in mpl_table.get_celld().items():
      if i == 0:
          cell.set_text_props(weight='bold', color='w')
          cell.set_facecolor(header_color)
      else:
          cell.set_facecolor(row_colors[i % len(row_colors)])
      cell.set_edgecolor(edge_color)




  saveName = name.replace(" ", "_")
  filename = f"{saveName}.png"
  plt.title(f"{name} (%)")
  # plt.tight_layout()
  plt.savefig(Path(folder) / filename, dpi=600)
  plt.show()
  plt.close()






def house_cum_sigma_banded_plot(assetRes, time, graphFigSize, houseHoldAssetsColoursCumPaths, householdDisplayLabels, titleWeight, folder, sampleSummary=None, ax=None):
  if ax == None:
    plt.figure(figsize=graphFigSize)

  timeLocal = time.copy()
  # if len(timeLocal) > 9130:
    #  timeLocal = timeLocal[(len(timeLocal)-9130):]
  sim_length = len(assetRes['portCumR'][households[0]])
  if len(timeLocal) > sim_length:
      timeLocal = timeLocal[-sim_length:]
  if sampleSummary != None:
    # sampleSummary = pd.DataFrame(sampleSummaryRows)
    makeTablePretty(sampleSummary, 'Sample Path Summary', folder)
  # for h in households:
  #   for path in assetRes['portSampleCum'][h]:
  #     # plottingList[h].append(path[-1])
  #     if h == '40-59':
  #       plt.plot(timeLocal, path*100, color=houseHoldAssetsColoursCumPaths[h], alpha=(alpha*1.3), linewidth=0.8)
  #     else:
  #       plt.plot(timeLocal, path*100, color=houseHoldAssetsColoursCumPaths[h], alpha=alpha, linewidth=0.8)
  #     # plottingList[h].append(path[-1]


  # plt.plot([], [], label=f"{householdDisplayLabels['0-20']}") #B R G
  # plt.plot([], [], label=f"{householdDisplayLabels['80-100']}")
  # plt.plot([], [], label=f"{householdDisplayLabels['40-59']}")
  zorders = {"80-100": 3, "40-59": 2, "0-20": 1}
  for h in households:
    for path in assetRes['portSampleCum'][h]:
      if h == '40-59':
        plt.plot(timeLocal, path*100, color=houseHoldAssetsColoursCumPaths[h], alpha=(0.2*1.3), linewidth=0.8, zorder=zorders[h])
      else:
        plt.plot(timeLocal, path*100, color=houseHoldAssetsColoursCumPaths[h], alpha=0.2, linewidth=0.8, zorder=zorders[h])

  # FIX: Explicitly assign colors to the legend handles
  plt.plot([], [], color=houseHoldAssetsColoursCumPaths['80-100'], label=f"{householdDisplayLabels['80-100']}")
  plt.plot([], [], color=houseHoldAssetsColoursCumPaths['40-59'], label=f"{householdDisplayLabels['40-59']}")
  plt.plot([], [], color=houseHoldAssetsColoursCumPaths['0-20'], label=f"{householdDisplayLabels['0-20']}")
  plt.title("Household Portfolio: Cumulative Return Paths", weight=titleWeight)
  plt.xlabel("Date")
  plt.ylabel("Cumulative Return (%)")
  plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(100.0))
  plt.grid(True, linestyle='--', alpha=0.7)
  plt.legend(title="HH Income Group")
  plt.savefig(os.path.join(folder, "cumRpaths.png"), dpi=600)
  plt.show()
  




def householdVolatilityPlot(graphFigSize, houseHoldAssetsColours, assetRes, time, folder):
  
  timeLocal = time.copy()
  # if len(timeLocal) > 9130:
  #    timeLocal = timeLocal[(len(timeLocal)-9130):]
  sim_length = len(assetRes['portCumR'][households[0]])
  if len(timeLocal) > sim_length:
      timeLocal = timeLocal[-sim_length:]
  x = pd.to_datetime(timeLocal)
  # x = time
  plt.figure(figsize=graphFigSize)
  # for h in households:
    # plt.plot(x, assetRes['portSigma'][h], label=f"{h} Household Volatility", color=houseHoldAssetsColours[h])
  zorders = {"80-100": 3, "40-59": 2, "0-20": 1}
  for h in households:
    plt.plot(x, assetRes['portSigma'][h], label=f"{h} Household Volatility", color=houseHoldAssetsColours[h], zorder=zorders[h])
  plt.title("Household Daily Volatility Over Time")
  plt.xlabel("Time")
  plt.ylabel("Volatility")
  plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
  plt.legend(
        loc="upper right",
        fontsize=15,          
        title_fontsize=17,    
        handlelength=1.5,     
        handleheight=1,    
        labelspacing=.6     
    )
  plt.grid(True)
  plt.savefig(os.path.join(folder, "householdVolatility.png"), dpi=600)
  plt.show()
# householdVolatility()

def assetClassVolatilityBar(graphFigSize, fullSavedAssetRes, assetClassColours, titleWeight, folder):
  
    
  # x = pd.to_datetime(time)
  assetClassVolatility = {}
  plt.figure(figsize=graphFigSize)
  sigmaList = []
  colourList = []
  labelList = []
  for assetClass in fullSavedAssetRes['sigmaAssetClassPath']:
    sigmaList.append(np.nanmean(fullSavedAssetRes['sigmaAssetClassPath'][assetClass]))
    labelList.append(f"{assetClass}")

    colourList.append(assetClassColours[assetClass])
  # plt.bar(label=f"{assetClass}", color=assetClassColours[assetClass], alpha=alpha)
  plt.bar(labelList, sigmaList, color=colourList)
  plt.title(f"Mean Asset Class Volatility", weight=titleWeight)
  plt.xlabel("Asset Class")
  plt.xticks(labelList, rotation=45, ha='right' )
  plt.ylabel("Volatility")
  plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
  plt.legend(
        loc="upper right",
        fontsize=15,          # smaller font (half if original was ~12)
        title_fontsize=17,    # smaller title
        handlelength=1.5,      # shorter legend lines
        handleheight=1,    # shrink vertical size of handles
        labelspacing=.6     # reduce vertical spacing between labels
    )
  plt.grid(False)
  plt.savefig(os.path.join(folder, "assetClassVolBar.png"), dpi=600)
  plt.show()
# assetClassVolatilityBar()



def plotMeanPath(meanPath, households, time, householdDisplayLabels, graphFigSize, houseHoldAssetsColours, titleWeight, folder):
  plt.figure(figsize= graphFigSize)
  
  timeLocal = time.copy()
  
  # meanPath is a dict, get the length from the first household's array
  sim_length = len(meanPath[households[0]])
  
  if len(timeLocal) > sim_length:
      timeLocal = timeLocal[-sim_length:]
      
  x = pd.to_datetime(timeLocal)

  # for h in households:
    # Use meanPath[h] to plot the specific array for the current household
    # plt.plot(x, meanPath[h], color=houseHoldAssetsColours[h], label=f"{householdDisplayLabels[h]}")
  zorders = {"80-100": 3, "40-59": 2, "0-20": 1}
  for h in households:
    plt.plot(x, meanPath[h], color=houseHoldAssetsColours[h], label=f"{householdDisplayLabels[h]}", zorder=zorders[h])
  plt.title("Cumulative Returns: Mean Household Path", weight=titleWeight)
  plt.xlabel("Date")
  plt.ylabel("Cumulative Return %")
  ax = plt.gca()
  ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
  
  plt.legend(
    loc="upper left",
    fontsize=20,          
    title_fontsize=22,    
    handlelength=2,      
    handleheight=1.5,    
    labelspacing=.8,     
    title="HH Income Group"
  )
  plt.xticks(rotation=45)
  plt.grid(True)
  plt.savefig(os.path.join(folder, "meanPath.png"), dpi=600)
  plt.show()
  
  # print(finalVals)
# meanHousePath()
def summaryTableShow(aggRes):
  summary = aggRes['summaryTable']
  makeTablePretty(summary, "Summary", folder, col_width=4)
  

def getWeightsTable(inputs, graphHeight, folder):
  assetWeights = inputs.get("assetWeights", inputs.get("asset_weights"))
  assetsCompleted = inputs.get("assetsCompleted", inputs.get("assets"))
  
  if assetWeights is None or assetsCompleted is None: 
      return
      
  inputs["assetWeights"] = assetWeights
  houseClassWeights = assetWeights 
  houseTable = []
  midHouseTable = []
  lowHouseTable = []
  tickersFlat = []

  for assetClass, tickers in assetsCompleted.items():

      # midWeights = []
      # lowWeights = []
      # Difference1 = []
      # Difference2 = []
      for ticker in tickers:
                  highWeights = inputs["assetWeights"]['80-100'][assetClass][ticker]
                  midWeights = inputs["assetWeights"]['40-59'][assetClass][ticker]
                  lowWeights = inputs["assetWeights"]['0-20'][assetClass][ticker]
                  Difference1 = inputs["assetWeights"]['80-100'][assetClass][ticker] - inputs["assetWeights"]['0-20'][assetClass][ticker] #, if not np.isnan(optW) else np.nan,
                  Difference2 = inputs["assetWeights"]['80-100'][assetClass][ticker] - inputs["assetWeights"]['40-59'][assetClass][ticker]#, if not np.isnan(optW) else np.nan


                  houseTable.append({
                                          'Asset Class': assetClass,
                                          'Asset': ticker,
                                          'Household 80-100 Weights': highWeights,
                                          'Household 40-59 Weights': midWeights,
                                          'Household 0-20 Weights': lowWeights,
                                          # 'Optimal Weights': optWeightsFlat[i] if i < len(optWeightsFlat) else np.nan,
                                          'Difference': Difference1, #if not np.isnan(optW) else np.nan,
                                          'Differences': Difference2#, if not np.isnan(optW) else np.nan
                                          })




  weightDF = pd.DataFrame(houseTable)
  # print(weightDF)


  # Define the columns to be formatted, using actual column names from houseTable
  numeric_cols = ['Household 80-100 Weights', 'Household 40-59 Weights', 'Household 0-20 Weights', 'Difference', 'Differences']


  def format_pct(x):
      if pd.notnull(x) and isinstance(x, (int, float, np.number)):
          return f"{x * 100:.2f}"
      return ""

  displayDF = weightDF.copy()
  for col in numeric_cols:
      displayDF[col] = displayDF[col].map(format_pct)

  print("")
  # print(weightDF)


  fig, ax = plt.subplots(figsize=(graphHeight, len(weightDF)*0.5))
  ax.axis('off')


  def weightColour(val):
    if np.isnan(val):
      return 'white'
    return plt.cm.Blues(val) if val >=0 else plt.cm.Greens(-val)


  tableValues = weightDF.copy()
  tbl = ax.table(cellText=tableValues.values, colLabels=tableValues.columns, loc='center')
  weightsNumeric = pd.DataFrame(houseTable)
  # print(weightsNumeric)
#   weightsDisplay = weightsNumeric.copy()
  weightsDisplay = displayDF.copy()
  tbl = ax.table(cellText=weightsDisplay.values, colLabels=weightsDisplay.columns, loc='center')



  for i, row in weightDF.iterrows():
    original_weight_data = pd.DataFrame(houseTable)


    # Get column indices dynamically from weightsDisplay
    col_80_100_idx = weightsDisplay.columns.get_loc('Household 80-100 Weights')
    col_40_59_idx = weightsDisplay.columns.get_loc('Household 40-59 Weights')
    col_0_20_idx = weightsDisplay.columns.get_loc('Household 0-20 Weights')
    col_diff_idx = weightsDisplay.columns.get_loc('Difference')
    col_diffs_idx = weightsDisplay.columns.get_loc('Differences')


    # Apply coloring based on original numeric values for Household Weights
    if pd.notnull(original_weight_data.loc[i, 'Household 80-100 Weights']):
      tbl[i+1, col_80_100_idx].set_facecolor(plt.cm.Greens(original_weight_data.loc[i, 'Household 80-100 Weights']))
    if pd.notnull(original_weight_data.loc[i, 'Household 40-59 Weights']):
      tbl[i+1, col_40_59_idx].set_facecolor(plt.cm.Blues(original_weight_data.loc[i, 'Household 40-59 Weights']))
    if pd.notnull(original_weight_data.loc[i, 'Household 0-20 Weights']):
      tbl[i+1, col_0_20_idx].set_facecolor(plt.cm.Oranges(original_weight_data.loc[i, 'Household 0-20 Weights']))


    # Apply coloring for 'Difference'
    diff = original_weight_data.loc[i, 'Difference']
    if pd.notnull(diff):
      min_diff = original_weight_data['Difference'].min()
      max_diff = original_weight_data['Difference'].max()
      if max_diff - min_diff != 0:
          normalized_diff = (diff - min_diff) / (max_diff - min_diff)
          tbl[i+1, col_diff_idx].set_facecolor(plt.cm.GnBu(normalized_diff))
      else:
          tbl[i+1, col_diff_idx].set_facecolor(plt.cm.GnBu(0.5))


    # Apply coloring for 'Differences'
    diff2 = original_weight_data.loc[i, 'Differences']
    if pd.notnull(diff2):
      min_diff2 = original_weight_data['Differences'].min()
      max_diff2 = original_weight_data['Differences'].max()


      if max_diff2 - min_diff2 != 0:
          normalized_diff2 = (diff2 - min_diff2) / (max_diff2 - min_diff2)
          tbl[i+1, col_diffs_idx].set_facecolor(plt.cm.RdPu(normalized_diff2))
      else:
          tbl[i+1, col_diffs_idx].set_facecolor(plt.cm.RdPu(0.5))


  tbl.auto_set_font_size(False)
  tbl.set_fontsize(10)
  tbl.scale(1, 1.5)
  plt.tight_layout()
  plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
  # Fix: Save the figure to a specific file within the folder
  plt.title("Household Asset Weights")
  plt.savefig(os.path.join(folder, 'assetHouseWeights.png'), dpi=300)
  plt.show()


  # ======================================================================================
  #                               Ticker Level Weights
  # ======================================================================================
  classTable = []
  midHouseTable = []
  lowHouseTable = []
  tickersFlat = []




  for assetClass, tickers in assetsCompleted.items():
      highWeights = []
      midWeights = []
      lowWeights = []
      Difference1 = []
      Difference2 = []
      for ticker in tickers:
                  highWeights.append(inputs["assetWeights"]['80-100'][assetClass][ticker])
                  midWeights.append(inputs["assetWeights"]['40-59'][assetClass][ticker])
                  lowWeights.append(inputs["assetWeights"]['0-20'][assetClass][ticker])
                  Difference1.append(inputs["assetWeights"]['80-100'][assetClass][ticker] - inputs["assetWeights"]['0-20'][assetClass][ticker]) #, if not np.isnan(optW) else np.nan,
                  Difference2.append(inputs["assetWeights"]['80-100'][assetClass][ticker] - inputs["assetWeights"]['40-59'][assetClass][ticker])#, if not np.isnan(optW) else np.nan


      classTable.append({
                              'Asset Class': assetClass,
                              # 'Asset': ticker,
                              'Household 80-100 Weights': sum(highWeights),
                              'Household 40-59 Weights': sum(midWeights),
                              'Household 0-20 Weights': sum(lowWeights),
                              # 'Optimal Weights': optWeightsFlat[i] if i < len(optWeightsFlat) else np.nan,
                              'Difference': sum(Difference1), #if not np.isnan(optW) else np.nan,
                              'Differences': sum(Difference2)#, if not np.isnan(optW) else np.nan
                              })




  weightDF = pd.DataFrame(classTable)
  # print(weightDF)


  # Define the columns to be formatted, using actual column names from houseTable
  numeric_cols = ['Household 80-100 Weights', 'Household 40-59 Weights', 'Household 0-20 Weights', 'Difference', 'Differences']


  # Apply formatting to the numeric columns using .map for a single series and .apply for multiple series
  # Or, iterate through columns if using a lambda with conditional formatting
  for col in numeric_cols:
      weightDF[col] = weightDF[col].map(
          lambda x: f"{x:.3f}" if pd.notnull(x) and isinstance(x, (int, float)) else ""
      )


  print("")
  # print(weightDF)


  fig, ax = plt.subplots(figsize=(graphHeight, len(weightDF)*0.5))
  ax.axis('off')


  def weightColour(val):
    if np.isnan(val):
      return 'white'
    return plt.cm.Blues(val) if val >=0 else plt.cm.Greens(-val)


  tableValues = weightDF.copy()
  tbl = ax.table(cellText=tableValues.values, colLabels=tableValues.columns, loc='center')
  weightsNumeric = pd.DataFrame(classTable)
  # print(weightsNumeric)
  weightsDisplay = weightDF.copy()
  tbl = ax.table(cellText=weightsDisplay.values, colLabels=weightsDisplay.columns, loc='center')
  # The getColumnColours function and the loop calling it are removed as they are redundant
  # and contain incorrect column references. The coloring logic is consolidated below.


  for i, row in weightDF.iterrows():
    original_weight_data = pd.DataFrame(classTable)


    # Get column indices dynamically from weightsDisplay (which has the formatted column names)
    col_80_100_idx = weightsDisplay.columns.get_loc('Household 80-100 Weights')
    col_40_59_idx = weightsDisplay.columns.get_loc('Household 40-59 Weights')
    col_0_20_idx = weightsDisplay.columns.get_loc('Household 0-20 Weights')
    col_diff_idx = weightsDisplay.columns.get_loc('Difference')
    col_diffs_idx = weightsDisplay.columns.get_loc('Differences')


    # Apply coloring based on original numeric values for Household Weights
    if pd.notnull(original_weight_data.loc[i, 'Household 80-100 Weights']):
      tbl[i+1, col_80_100_idx].set_facecolor(plt.cm.Greens(original_weight_data.loc[i, 'Household 80-100 Weights']))
    if pd.notnull(original_weight_data.loc[i, 'Household 40-59 Weights']):
      tbl[i+1, col_40_59_idx].set_facecolor(plt.cm.Blues(original_weight_data.loc[i, 'Household 40-59 Weights']))
    if pd.notnull(original_weight_data.loc[i, 'Household 0-20 Weights']):
      tbl[i+1, col_0_20_idx].set_facecolor(plt.cm.Oranges(original_weight_data.loc[i, 'Household 0-20 Weights']))


    # Apply coloring for 'Difference'
    diff = original_weight_data.loc[i, 'Difference']
    if pd.notnull(diff):
      min_diff = original_weight_data['Difference'].min()
      max_diff = original_weight_data['Difference'].max()
      if max_diff - min_diff != 0:
          normalized_diff = (diff - min_diff) / (max_diff - min_diff)
          tbl[i+1, col_diff_idx].set_facecolor(plt.cm.GnBu(normalized_diff))
      else:
          tbl[i+1, col_diff_idx].set_facecolor(plt.cm.GnBu(0.5))


    # Apply coloring for 'Differences'
    diff2 = original_weight_data.loc[i, 'Differences']
    if pd.notnull(diff2):
      min_diff2 = original_weight_data['Differences'].min()
      max_diff2 = original_weight_data['Differences'].max()


      if max_diff2 - min_diff2 != 0:
          normalized_diff2 = (diff2 - min_diff2) / (max_diff2 - min_diff2)
          tbl[i+1, col_diffs_idx].set_facecolor(plt.cm.RdPu(normalized_diff2))
      else:
          tbl[i+1, col_diffs_idx].set_facecolor(plt.cm.RdPu(0.5))


  tbl.auto_set_font_size(False)
  tbl.set_fontsize(10)
  tbl.scale(1, 1.5)
  plt.tight_layout()
  plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
  # Fix: Save the figure to a specific file within the folder
  plt.title("Household Asset Class Weights")
  plt.savefig(os.path.join(folder, 'assetClassHouseWeights.png'), dpi=300)
  plt.show()


  # =====================================================================================
  #                                   Bar Chart
  # =====================================================================================


def householdWeightsBar(
      weightsData: dict,
      assets: dict,
      households: list,
      householdColors: dict,
      graphFigSize,
      aggRes: dict,
      folder: str 

      ):
  # households = ["0-20", "40-59", "80-100"]
  # weightsData = inputs["assetWeights"]
  print(weightsData["80-100"])
  weightsDF = pd.DataFrame(weightsData)
  print(weightsDF)
  # Shares
  # Household main residence
  # Other real estate
  # Savings
  # Bonds/mutual funds
  # assets = ["Shares", "Household main residence", "Other real estate", "Savings", "Bonds/mutual funds", "Business Wealth"]


  # Mapping from detailed asset classes/tickers to broader categories
  assetCategoryMapping = {
      "Shares": ["Equities"],
      "Household main residence": [("Property", "Land HMR")],
      "Other real estate": [("Property", "Land Other"), ("Property", "Land")],
      "Savings": ["Deposits"],
      "Bonds/mutual funds": ["Bonds Short", "Bonds Long"],
      "Business Wealth": ["Business Wealth", "Business Wealth S.E"],
  }

  plot_categories = list(assetCategoryMapping.keys())
  allocations = {}
  for h in households:
    allocations[h] = {assetCategory: 0.0 for assetCategory in plot_categories} # Initialising with 0.0


    for broadCategory, sources in assetCategoryMapping.items():
      for source in sources:
        if isinstance(source, tuple): # Specific ticker within an asset class, e.g., ("Property", "Land HMR")
          assetClass, tickerName = source
          if assetClass in weightsData[h] and tickerName in weightsData[h][assetClass]:
            allocations[h][broadCategory] += weightsData[h][assetClass][tickerName]
        else: # Entire asset class, e.g., "Equities"
          assetClass = source
          if assetClass in weightsData[h]:
            allocations[h][broadCategory] += np.sum(list(weightsData[h][assetClass].values()))


  benchmark = "80-100"


  # Ensure `data` contains numerical values for all households and assets
  data = np.array([[allocations[h][a] for a in plot_categories] for h in households])


  x = np.arange(len(plot_categories))
  width = 0.25


  plt.figure(figsize=graphFigSize)


  # houseHoldColours = {
  #     "80-100": "tab:green",
  #     "0-20": "tab:blue",
  #     "40-59": "tab:red"
  # }
  houseHoldColours = {
        "80-100": "tab:red",
        "0-20": "tab:blue",
        "40-59": "tab:green"
    }

  valuesTotal = {}
  for i, h in enumerate(households):
    valuesTotal[h] = 0


  for i, h in enumerate(households):
    current_household_values = [allocations[h][a] for a in plot_categories]
    values = np.array(current_household_values)
    valuesTotal[h] += values
    if h == benchmark:
      highValues = values
    else:
      highValues = np.array([allocations[benchmark][a] for a in plot_categories])


    # Solid portion
    plt.bar(x + i*width, values, width, label=h, color=houseHoldColours[h])


    if h != benchmark:
      gap = np.maximum(0, (highValues - values))
      plt.bar(x + i*width, gap, width, bottom=values, alpha=0.2, color=houseHoldColours[h])


    for j in range(len(plot_categories)):
      values[j] = values[j]
      if values[j] > 0.005: # Only add label for values greater than 0.5% to avoid clutter
        plt.text(x[j] + i*width, values[j] + 0.01, f"{values[j]*100:.0f}%", ha='center', fontsize=12)






  plt.xticks(x + width, plot_categories, rotation=35, ha='right')
  plt.ylabel("Allocation (%)")
  ax = plt.gca()
  ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
  # plt.ylim(0.1) # Removed as it might cut off bars or set incorrect limits
  plt.title("Portfolio Allocation by Household", weight='bold')#\n(Gap Shaded Relative to 80-100)")
  plt.text(
      0.5, .96, #center, height
      "(Gap Shaded Relative to Top Household)",
      ha='center', va='bottom',
      transform=plt.gca().transAxes, # relative to axis
      fontsize=14,
  )
  plt.ylim(0, 1)
  # plt.set_fontsize(12)
  # plt.legend(title="Household")


  plt.legend(
      loc="upper right",
      fontsize=16,          
      title_fontsize=18,   
      handlelength=3,     
      handleheight=3,    
      labelspacing=0.9,
      title='HH Income Group' 
  )
  plt.tight_layout()
  if folder:
      plt.savefig(os.path.join(folder, "Portfolio_Allocation_Bar.png"), dpi=300)
  plt.show()


  print(f"valuesTotal {valuesTotal}")
  for i, h in enumerate(households):
    print(sum(valuesTotal[h]))

  # plt.figure(figsize=(12, 8))
  # plt.xticks(x + width, assets, rotation=25, ha='right')
  # plt.bar(x + i*width, valuesTotal, width, label=h, color='#FFFF00')
  # plt.show()
  # householdWeightsBar()


  # assets = ["Shares", "Household main residence", "Other real estate", "Savings", "Bonds/mutual funds", "Business Wealth"]


  # Mapping from detailed asset classes/tickers to broader categories
  # assetCategoryMapping = {
  #     "Shares": ["Equities"],
  #     "Household main residence": [("Property", "Land HMR")],
  #     "Other real estate": [("Property", "Land Other")],
  #     "Savings": ["Deposits"],
  #     "Bonds/mutual funds": ["Bonds Short", "Bonds Long"],
  #     "Business Wealth": ["Business Wealth", "Business Wealth S.E"]
  # }

def plot_gap_geometric(labels, gaps, rich_vals, poor_vals, folder=None):
    colors = ["#1a7f37" if g > 0 else "#b22222" for g in gaps]


    fig, ax = plt.subplots(figsize=(14,7))
    bars = ax.bar(labels, gaps, color=colors, edgecolor='black', linewidth=1.2)


    for bar, r, p, g in zip(bars, rich_vals, poor_vals, gaps):


        height = bar.get_height()
        label_text = f"{r:.1f}% vs {p:.1f}%"


        offset = max(abs(gaps)) * 0.03


        if g > 0:
            ax.text(bar.get_x() + bar.get_width()/2,
                    height + offset,
                    label_text,
                    ha='center', va='bottom',
                    fontsize=15, fontweight='bold')
        else:
            ax.text(bar.get_x() + bar.get_width()/2,
                    height - offset,
                    label_text,
                    ha='center', va='top',
                    fontsize=15, fontweight='bold')


    ax.axhline(0, color='black', linewidth=1.3)


    ax.set_ylabel("Contribution to Final Wealth Gap (%)", fontsize=20)
    ax.set_title(
        "Asset Contributions to Wealth Divergence\nTop 20% vs Bottom 20%",
        fontsize=25,
        fontweight='bold'
    )


    ax.grid(axis='y', linestyle='--', alpha=0.3)


    padding = max(abs(gaps)) * 0.25
    ax.set_ylim(min(gaps) - padding, max(gaps) + padding)


    plt.xticks(rotation=20, ha='right')
    plt.tight_layout()
    if folder:
        import os
        plt.savefig(os.path.join(folder, "Geometric_Gap_Contributions.png"), dpi=300)
    plt.show()

import matplotlib.ticker as mtick

# def _streamline_results(full_output):
#     item = {}

#     for category, analyses in full_output.items():
#         if not isinstance(analyses, dict):
#             continue

#         item[category] = {}

#         for analysis_name, analysis_data in analyses.items():
#             if isinstance(analysis_data, dict):
#                 if "raw" in analysis_data:
#                     item[category][analysis_name] = analysis_data["raw"]
#                 else:
#                     item[category][analysis_name] = analysis_data

#     return item

# def _streamline_results(full_output):
#   item = {}
  
#   # 1. Loop through top-level buckets: 'results', 'validation', etc.
#   for category, analyses in full_output.items():
#       if not isinstance(analyses, dict):
#           continue
          
#       # 2. Loop through analysis blocks: 'mean_household_results', 'house_vol_results', etc.
#       for analysis_name, analysis_data in analyses.items():
#           if isinstance(analysis_data, dict):
              
#               # Check if 'raw' and bubble it up
#               if 'raw' in analysis_data:
#                   item[analysis_name] = analysis_data['raw']
#               # elif 'core' in analysis_data:
#                   # item[analysis_name] = analysis_data['core']
#               else:
                  
#                   item[analysis_name] = analysis_data
                  
#   return item
def _streamline_results(full_output):
    streamlined = {}

    for section_name, section in full_output.items():

        if not isinstance(section, dict):
            streamlined[section_name] = section
            continue

        streamlined[section_name] = {}

        for analysis_name, analysis_data in section.items():

            if (
                isinstance(analysis_data, dict)
                and "raw" in analysis_data
            ):
                streamlined[section_name][analysis_name] = analysis_data["raw"]
            else:
                streamlined[section_name][analysis_name] = analysis_data

    return streamlined
def runGraphs(aggRes, assetResults, time, households, graph_dir, metric_results, tablesNeeded=True, plots_to_generate=None):
  folder = graph_dir #"/content/drive/MyDrive/Young_Economist/graphs"
  if not os.path.exists(folder):
    os.makedirs(folder)
    print("huh")
  graphFigSize = (14,6)
  alpha = 0.2
  titleWeight = 'normal'
  graphHeight = 14
  fullSavedAssetRes = assetResults
  # plt.rcParams.update({
  #     'font.family': 'DejaVu Sans',
  #     'font.size': 16,
  #     'axes.titlesize': 27,
  # #title
  #     'axes.labelsize': 24,
  #     'xtick.labelsize': 16,
  #     'ytick.labelsize': 16,
  #     'legend.fontsize': 16,
  #     'legend.title_fontsize': 15,
  #     'figure.titlesize': 26,
  #     'axes.spines.top': False,
  #     'axes.spines.right': False,


  #     'axes.grid': True




  #   })

  plt.rcParams.update({
      'font.family': 'DejaVu Sans',
      'font.size': 12,             
      'axes.titlesize': 16,        
      'axes.labelsize': 14,        
      'xtick.labelsize': 11,
      'ytick.labelsize': 11,      
      'legend.fontsize': 11,        
      'legend.title_fontsize': 12,  
      'figure.titlesize': 18,       
      'axes.spines.top': False,
      'axes.spines.right': False,
      'axes.grid': True
  })
  householdDisplayLabels = {
      "0-20": "0–20th Income Percentile",
      "40-59": "40–59th Income Percentile",
      "80-100": "80–100th Income Percentile"
  }


  assetRes = aggRes
  assetClassColours = {
      "Equities": "tab:red",
      "Bonds Short": "tab:blue",
      "Bonds Long": "tab:purple",
      "Property": "tab:orange",
      "Deposits": "tab:green",
      "Business Wealth": "#FFD700"
  # "Equities", "Bonds Short": "tab:blue", "Bonds Long": "tab:purple", "Property": "tab:orange", "Deposits"
  }
  houseHoldAssetsColours = {
      "80-100": "tab:red",
      "0-20": "tab:blue",
      "40-59": "tab:green"
  }




  

  x = pd.to_datetime(time)
  plottingList = {}
  currentPath = []
  currentHousehold = []


  # for path in mc["sampleHouseholdCum"]:
  #   for household in path:
  #     print(f"Household == {household}")
  #     plottingList[household] = {}


  # plottingList = {
  #     '80-100': {h: [] for h in households},
  #     '40-59': {h: [] for h in households},
  #     '0-20': {h: [] for h in households}
  # }
  # plottingList = {
  #     '80-100': [],
  #     '40-59': [],
  #     '0-20': []
  # }
  minValue = {
      '80-100': 0,
      '40-59': 0,
      '0-20': 0
  }
  maxValue = {
      '80-100': 0,
      '40-59': 0,
      '0-20': 0
  }
  minList = {
      '80-100': [],
      '40-59': [],
      '0-20': []
  }
  maxList = {
      '80-100': [],
      '40-59': [],
      '0-20': []
  }


  houseHoldAssetsColours = {
      "80-100": "tab:red",
      "0-20": "blue",
      "40-59": "tab:green"
  }
  houseHoldAssetsColoursCumPaths = {
      "80-100": "crimson",
      "0-20": "mediumblue",
      "40-59": "green"
  }
  houseHoldAssetsColoursIntense = {
      "80-100": "deeppink",
      "0-20": "c",
      "40-59": "lime"
  }
  assetClassColours = {
      "Equities": "tab:red",
      "Bonds Short": "tab:blue",
      "Bonds Long": "tab:purple",
      "Property": "tab:orange",
      "Deposits": "tab:green",
      "Business Wealth": "#FFD700"
  # "Equities", "Bonds Short": "tab:blue", "Bonds Long": "tab:purple", "Property": "tab:orange", "Deposits"
  }

  if plots_to_generate is None:
        plots_to_generate = [
            "wealth_gap", "band_heatmap", "crps", "convergence", 
            "mean_path", "volatility", "asset_vol_bar", "tables", "household_cum_paths"
        ]

  #render 
  metric_results = copy.deepcopy(metric_results)
  metric_results_streamlined = _streamline_results(metric_results)
  print(metric_results_streamlined.keys())
  # results = metric_results_streamlined.get("results")
  # if results is None:
  #     results = metric_results_streamlined
   #
  if "results" in metric_results_streamlined:
      results = metric_results_streamlined["results"]
  else:
      results = metric_results_streamlined
  
  print("[DEBUG] top-level keys:", metric_results_streamlined.keys())
  print("[DEBUG] results alias keys:", results.keys())
  if "results" in metric_results_streamlined:
      print(metric_results_streamlined["results"].keys())
  else:
      print("NO RESULTS KEY")
  if not ("results" in metric_results_streamlined):
    results = metric_results_streamlined
    # results = metric_results_streamlined["results"]#.get(metric_results["results"])
    # results = _streamline_results(metric_results)
  if "house_cum_results" in results:
    df = results["house_cum_results"].get("house_cum_df")
    try:
        house_cum_sigma_banded_plot(
          assetRes=aggRes,
          time=time,
          graphFigSize=graphFigSize,
          houseHoldAssetsColoursCumPaths=houseHoldAssetsColoursCumPaths,
          householdDisplayLabels=householdDisplayLabels,
          titleWeight=titleWeight,
          folder=graph_dir 
        )
    except Exception as e:
        print(f"Warning: Cumulative paths plot failed: {e}")
    
    if tablesNeeded and df is not None:
        makeTablePretty(df, 'Household Cumulative Returns', graph_dir)

  # 2. Household Volatility
  if "house_vol_results" in results:
      df = results["house_vol_results"].get("house_vol_df")
      householdVolatilityPlot(graphFigSize, houseHoldAssetsColours, aggRes, time, graph_dir)
      if tablesNeeded and df is not None:
          makeTablePretty(df, 'Household Volatility', graph_dir)

  # 3. Asset Class Volatility
  if "asset_vol_results" in results:
      df = results["asset_vol_results"].get("assetVol_df")
      assetClassVolatilityBar(
          graphFigSize=graphFigSize,
          fullSavedAssetRes=assetResults,
          assetClassColours=assetClassColours,
          titleWeight=titleWeight,
          folder=graph_dir
      )
      if tablesNeeded and df is not None:
          makeTablePretty(df, 'Asset Class Volatility', graph_dir)

  # 4. Mean Paths
  if "mean_household_results" in results:
      df = results["mean_household_results"].get("meanSummary_df")
      mean_path = results["mean_household_results"].get("meanPath", results["mean_household_results"].get("mean_path"))
      
      if mean_path is not None:
          plotMeanPath(
            meanPath=mean_path,
            households=households,
            time=time,
            householdDisplayLabels=householdDisplayLabels,
            graphFigSize=graphFigSize,
            houseHoldAssetsColours=houseHoldAssetsColours,
            titleWeight=titleWeight,
            folder=graph_dir
          )
      if tablesNeeded and df is not None:
          makeTablePretty(df, 'Mean Path Final Returns', graph_dir)

  # 5. Geometric Gap Results
  if "gap_geometric_results" in results:
      results_raw = results["gap_geometric_results"].get("raw", results["gap_geometric_results"])
      labels = results_raw.get("labels")
      rich_vals = results_raw.get("rich_vals")
      poor_vals = results_raw.get("poor_vals")
      gaps = results_raw.get("gaps")
      summary_df = results["gap_geometric_results"].get("summary_df")

      if tablesNeeded and summary_df is not None:
          makeTablePretty(summary_df, "Geometric Wealth Gap Summary", graph_dir)
          
      if gaps is not None and labels is not None:
          try:
              plot_gap_geometric(labels, gaps, rich_vals, poor_vals, folder=graph_dir)
          except Exception as e:
              print(f"Warning: Geometric contribution plot failed: {e}")

  # 6. Overall Gap Dist
  if "gap_results" in results:
      pairs = results["gap_results"].get("pairs")
      summary_df = results["gap_results"].get("summary_df")
      prob_positive = results["gap_results"].get("prob_positive")
      
      if pairs is not None and summary_df is not None:
          plot_wealth_gap_dist(pairs, summary_df, prob_positive, graph_dir)

  # 7. Validation Data Blocks (Now accessing the flattened dict directly)
  path_number = "" # Safety initialization
  
  if "convergence_results" in results:
      convergence_df = results["convergence_results"].get("convergence_df")
      path_number = results["convergence_results"].get("path_number", "")
      if convergence_df is not None:
          plot_monte_carlo_convergence(convergence_df, graph_dir, households, path_number)
    
  if "back_test_results" in results:
      backtest_df = results["back_test_results"].get("backtest_df")
      backtest_raw = results["back_test_results"].get("backtest_raw")
      sim_low_pct = results["back_test_results"].get("sim_low_pct", 5.0)
      sim_high_pct = results["back_test_results"].get("sim_high_pct", 95.0)
      
      if backtest_raw is not None:
          backtest_distribution_plot(backtest_df, households, backtest_raw, sim_low_pct, sim_high_pct, path_number, graph_dir)

  if "crps_results" in results:
      crps_scores = results["crps_results"].get("crps_scores")
      crps_per_window = results["crps_results"].get("crps_per_window")
      
      if crps_scores is not None and crps_per_window is not None:
          CRPS_bar_chart(crps_scores, crps_per_window, graph_dir)
      
      crps_df = results["crps_results"].get("crps_df")
      if tablesNeeded and crps_df is not None:
          _make_table_pretty(crps_df, "CRPS Summary", folder)
    
  if "band_results" in results:
      coverage_df = results["band_results"].get("coverage_df")
      # Convergence results is at the same flat level now
      sim_one_year = results.get("convergence_results", {}).get("sim_horizon")
      hist_one_year = results.get("convergence_results", {}).get("hist_horizon")
      band_names = results["band_results"].get("band_names")
      expected = results["band_results"].get("expected")
      coverage = results["band_results"].get("coverage_raw")
      
      if coverage is not None and expected is not None:
          getHeatMap(
            households = households,
            coverage_df = coverage_df,
            coverage = coverage,
            sim_one_year = sim_one_year,
            hist_one_year = hist_one_year,
            band_names = band_names,
            expected = expected,
            folder = graph_dir
          )
      if tablesNeeded and coverage_df is not None:
          _make_table_pretty(coverage_df, "Multi-Band Backtest Coverage", graph_dir)
  
  # 8. Weight Inputs Block
  assets = results.get("assetsCompleted", results.get("assets", None))
  asset_weights_raw = results.get("assetWeights", results.get("asset_weights"))
  
  try:
      # getWeightsTable looks for an inputs dict with "assetWeights" inside.
      # Because results is flattened, results["assetWeights"] satisfies this perfectly!
      getWeightsTable(results, graphHeight, folder)
  except Exception as e:
      print(f"Warning: getWeightsTable failed: {e}")
      
  try:
      if asset_weights_raw is not None and assets is not None:
          householdWeightsBar(asset_weights_raw, assets, households, houseHoldAssetsColours, graphFigSize, aggRes, graph_dir)
  except Exception as e:
      print(f"[WARN] householdWeightsBar failed: {e}")

    # ================================================================================
  

import numpy as np
import arch
print("arch.__version__:", arch.__version__)


import datetime as dt


import pandas as pd
# from google.colab import files
# import pandas_datareader.data as web
from arch import arch_model

import os
import pickle
import numpy as np
import gc
import pickle
# from google.colab import drive
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.pyplot
import matplotlib.cm as cm
import numpy as np
import datetime as dt
from matplotlib.ticker import PercentFormatter
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.ticker as mtick
from matplotlib.ticker import PercentFormatter
# !pip install scipy
from scipy.optimize import minimize
from scipy.stats import t as studentT

import arch
import warnings
from arch.utility.exceptions import DataScaleWarning
from arch.utility.exceptions import ConvergenceWarning

import io # Import the io module
from numba import njit
import numpy as np
import pandas as pd
import os
import pickle

  # if alreadyRun != 1:
from numba import njit
import copy
import matplotlib.cm as cm
import os
import tqdm
tqdm.tqdm = lambda *args, **kwargs: None
# !pip install pandas_datareader.data
# !pip install yfinance
import yfinance as yf
# yf.tqdm.tqdm = lambda *args, **kwargs: args[0] if args else None
# yf.utils.disable_progress_bar()


# !pip install arch
# !pip install numpy
# !pip install matplotlib


# !pip install warnings
# !pip install arch.utility

warnings.simplefilter("ignore", DataScaleWarning)
warnings.simplefilter("ignore", FutureWarning)
warnings.simplefilter("ignore", ConvergenceWarning)
from tqdm.auto import tqdm
tqdm.__init__ = lambda *args, **kwargs: None


import matplotlib.pyplot as plt
import os
os.environ["TQDM_DISABLE"] = "1"

# =============================================================================================================================================

#   Configuration 

# =============================================================================================================================================
debug2 = False
debug3 = False
debug4 = False # z
debug5 = False #minimal
debug6 = False #start up
debug7 = False
debug8 = False #(first Eps, etc)
debug9 = False # property stuff for r
debug10 = False # alpha, beta, etc
debug11 = False
debug12 = False
debugBus = False
debug14 = False
debugVolatility2 = False
debugVol3 = False
debug = False
optRun = False
debugLocal = False # shorter run
debugCorrelation = False # correlation in runPort and apply correlation 
sigma_list_debug = False
useLogs = True
useCholesky = False
useBlending = True
hardCrash = False
import logging

from matplotlib.ticker import PercentFormatter
from scipy.optimize import minimize
# assetsYahoo = {
#           "Equities": {
#             '^GSPC',
#             '^FTSE',
#             '^STOXX',
#             '^IETP',
#             'IWDA.L',
#                 },
#           "Bonds Short": {
#               # 'IB01.L',
#               'SHY',
#               'IGLS.L',
#               'SYB3.SW',
#               'IAGG',
#                 },
#           "Bonds Long": {
#               'IEF',
#               'IGLT.L',
#               'SYBB.DE',
#               'EUN3.DE',
#               }
#               }
# for ac in assetsYahoo:
#   for ticker in assetsYahoo[ac]:
#     ticker_obj = yf.Ticker(ticker)
#     hist = ticker_obj.history(period="max")

#     print(
#         ticker,
#         hist.index.min(),
#         hist.index.max(),
#         len(hist)
#     )
      # data = yf.download(ticker, progress=False)

      # print(
      #     ticker,
      #     data.index.min(),
      #     data.index.max(),
      #     len(data)
      # )
def setup():
  
#   from google.colab import drive
#   drive.mount('/content/drive')
  debugLite = False
  debugDeep = False
  


  nTotalPaths = 600
  nSamplePaths = 300
  expectedLength = 9130
  households = ["80-100", "40-59", "0-20"]


  folder = data_dir #"/content/drive/MyDrive/Young_Economist"
  households = ["80-100", "40-59", "0-20"]
  samplePathsPerHousehold = 150  # for plotting only
  floatType = np.float32
  maxPathsToLoad = 4000  # stop after this many Monte Carlo paths
  debug = False
  chunkFolder = data_dir / "chunkResults" #"/content/drive/MyDrive/Young_Economist/chunkResults"


  pathCounts = [100, 200, 300, 800, 1300, 1800, 2000, 2500, 3000]
  pathCountsConverge = [100, 200, 300, 2000, 2500, 3000, 4000, 4500]
  pathCountsConverge = [4999]
  pathCounts = pathCountsConverge
  
  # import os
  # ----------------------------
  # Helper functions
  # ----------------------------
  def _loadChunk(filePath):
      with open(filePath, "rb") as f:
          return pickle.load(f)['chunkResults']


  def _saveAggregationState(state, filePath):
      filename_from_path = os.path.basename(filePath)
      if os.path.dirname(filePath):
        os.makedirs(os.path.dirname(filePath), exist_ok=True)


      if os.path.isdir(filePath):
          print(f"Warning: Removing existing directory named '{filename_from_path}' at '{filePath}'.")
          os.rmdir(filePath)


      with zstd.open(filePath, "wb") as f:
          pickle.dump(state, f)
      print(f"Aggregation state saved to {filePath}.")


  def _loadAggregationState(filePath):
      filename_from_path = os.path.basename(filePath)
      if os.path.isdir(filePath):
          print(f"Warning: Removing existing directory named '{filename_from_path}' at '{filePath}'.")
          os.rmdir(filePath)
      if not os.path.exists(filePath):
          print(f"No previous aggregation state found at {filePath}.")
          return None


      try:
          try:
              with zstd.open(filePath, "rb") as f:
                  state = pickle.load(f)
          except zstd.ZstdError:
              with open(filePath, "rb") as f:
                  state = pickle.load(f)
          print(f"Previous aggregation state loaded from {filePath}. State None? {state is None}")
          return state
      except EOFError:
          print(f"EOFError: The file {filePath} is empty or corrupted. Cannot load state.")
          return None
      except Exception as e:
          print(f"An unexpected error occurred while loading state from {filePath}: {e}")
          return None


  # fullSavedAssetResFull = _loadAggregationState(filePath = data_dir / "assetState3ResultsLight.pkl")
  # fullSavedAssetRes = fullSavedAssetResFull


  reRun = 1
 # !pip install warnings
  # !pip install arch.utility
  # import warnings
  # from arch.utility.exceptions import DataScaleWarning
  # warnings.simplefilter("ignore", DataScaleWarning)
  # warnings.simplefilter("ignore", FutureWarning)
  # import numpy as np


  # import os
  # os.environ["TQDM_DISABLE"] = "1"
  debug2 = False
  debug3 = False
  debug4 = False # z
  debug5 = False #minimal
  debug6 = False #start up
  debug7 = False
  debug8 = False #(first Eps, etc)
  debug9 = False # property stuff for r
  debug10 = False # alpha, beta, etc
  debug11 = False
  debug12 = False
  debugBus = False
  debug14 = False
  debugVolatility2 = False
  debugVol3 = False
  debug = False
  optRun = False
  # import pickle
  alreadyRun = 12
  daysPerYear = 365





  # if 10 == 1:


    # uploaded = files.upload()


    # for fn in uploaded.keys():
    #   # Read the excel file directly from the bytes content
    #   df = pd.read_excel(io.BytesIO(uploaded[fn]))
    #   if debug6 == True:
    #     print(df)
    #   break # Exit loop after processing the first file


#   from google.colab import drive
#   drive.mount('/content/drive')
  folder = data_dir #"/content/drive/MyDrive/Young_Economist"


  if os.path.exists(folder):
    if debug6 == True:
      print("data_dir exists")
  if not os.path.exists(folder):
    os.makedirs(folder)
    print("huh")

  weightsLocation = "household_asset_weights.xlsx"
  pathWoo = data_dir / weightsLocation #"/content/drive/MyDrive/Young_Economist/exampleFile.xlsx"
  if os.path.exists(pathWoo):
    if debug6 == True:
      print("WOOO IT EXISTS. GOSH!!")
  if not os.path.exists(pathWoo):
    raise FileNotFoundError(f"{weightsLocation} not found")
  df = pd.read_excel(pathWoo)


  listD10 = df.iloc[3, 1:].tolist()
  if debug6 == True:
    print("Data from row with index 0, from column index 2 onwards:")
    print(listD10)
  if debug6 == True:
    print(listD10)


  listD2 = df.iloc[4, 1:].tolist()


  # print(listD2)




  listD6 = df.iloc[5, 1:].tolist()


  # print(listD6)
  if debug6 == True:
    print(listD2)
    print("Second household")
    print(listD6)








  # start = dt.datetime(2000, 1, 1)
  # end = dt.datetime(2025, 1, 1)
  # time = []
  # for i in range((end - start).days):
  #   time.append(start + dt.timedelta(days=i))
  # extraTime = []
  # for i in range((end - (start - dt.timedelta(days=1))).days):
  #   extraTime.append((start - dt.timedelta(days=1)) + dt.timedelta(days=i))

  # res = fullSavedAssetRes['sampleAssetPaths']['Business Wealth']['Business Wealth S.E'][1]

  # # Build a time axis that matches res exactly, regardless of resolution
  # res_len = len(res)
  # total_days = (end - start).days          # 9130
  # step = total_days / res_len              # 10.0 now, 1.0 when you switch to 1:1
  # res_time = [start + dt.timedelta(days=i * step) for i in range(res_len + 2)]

  # plt.title("WOOO HERE")
  # plt.plot(res_time, res)
  # plt.show()
  # time = res_time
  # res = fullSavedAssetRes['sampleAssetPaths']['Business Wealth']['Business Wealth S.E'][1]
  # plt.title("WOOO HERE 2")
  # plt.plot(time[2:], res)
  # plt.show()

  alpha = 0.15




  # assets = {
  #     "Equities": {
  #         '^GSPC': '^GSPC',
  #         '^STOXX': '^STOXX',
  #         '^IETP': '^IETP'
  #         },
  #     #S and P, Eur Stoxx 600, Irish 20
  #     "Bonds" : {'AGG': 'AGG',
  #                'SPFF.DE': 'SPFF.DE',
  #                'SYB4.DE': 'SYB4.DE'},d
  #     # US, Global (not Corp differnciated + Eur Based), and Eur-Area
  #     "Deposit": {
  #      "Deposit": "Deposit"
  #     }


  #     }


  classWeightsHousehold = {
      "Equities": 0.33,
      "Bonds": 0.24,
      "Deposit": .43
  }








  households = ["80-100", "40-59", "0-20"] #, HouseName]
  # assetClass = ["Equities", "Bonds Short", "Bonds Long", "Property", "Deposits"]

  
  assetWeights = {
      "80-100": {
          "Equities": {
            '^GSPC': listD10[0],
            '^FTSE': listD10[1],
            '^STOXX': listD10[2],
            '^IETP': listD10[3],
            '^990100-USD-STRD': listD10[4],
                },
          "Bonds Short": {
              # 'IB01.L': listD10[5],
              'SHY': listD10[5],
              'IGLS.L': listD10[6],
              'SYB3.SW': listD10[7],
              'Ire Short': listD10[8],
              'IAGG': listD10[9],
                },
          "Bonds Long": {
              'IEF': listD10[10],
              'IGLT.L': listD10[11],
              'SYBB.DE': listD10[12],
              'Ire Long': listD10[13],
              'EUN3.DE': listD10[14],
              },
          "Property":{
              'Land Overall': listD10[15],
              'Land HMR': listD10[16],
              'Land': listD10[17],
              'Land Other': listD10[18],
              'Land UK': listD10[19],
          },
          "Deposits":{
              'Overnight_Ire': listD10[20],
              'ReedemableAtNotice': listD10[21],
              'Agreed Maturity < 2': listD10[22],
              'Agreed Maturity > 2': listD10[23],
              },
          "Business Wealth":{
              "Business Wealth S.E": listD10[24],
          }
          },
      "0-20": {
          "Equities": {
            '^GSPC': listD2[0],
            '^FTSE': listD2[1],
            '^STOXX': listD2[2],
            '^IETP': listD2[3],
            '^990100-USD-STRD': listD2[4],
                },
          "Bonds Short": {
              # 'IB01.L': listD2[5],
              'SHY': listD2[5],
              'IGLS.L': listD2[6],
              'SYB3.SW': listD2[7],
              'Ire Short': listD2[8],
              'IAGG': listD2[9],
                },
          "Bonds Long": {
              'IEF': listD2[10],
              'IGLT.L': listD2[11],
              'SYBB.DE': listD2[12],
              'Ire Long': listD2[13],
              'EUN3.DE': listD2[14],
              },
          "Property":{
              'Land Overall': listD2[15],
              'Land HMR': listD2[16],
              'Land': listD2[17],
              'Land Other': listD2[18],
              'Land UK': listD2[19],
          },
          "Deposits":{
              'Overnight_Ire': listD2[20],
              'ReedemableAtNotice': listD2[21],
              'Agreed Maturity < 2': listD2[22],
              'Agreed Maturity > 2': listD2[23],
          },
          "Business Wealth":{
              "Business Wealth S.E": listD2[24],
          }
          },
      "40-59": {
          "Equities": {
            '^GSPC': listD6[0],
            '^FTSE': listD6[1],
            '^STOXX': listD6[2],
            '^IETP': listD6[3],
            '^990100-USD-STRD': listD6[4],
                },
          "Bonds Short": {
              # 'IB01.L': listD6[5],
              'SHY': listD6[5],
              'IGLS.L': listD6[6],
              'SYB3.SW': listD6[7],
              'Ire Short': listD6[8],
              'IAGG': listD6[9],
                },
          "Bonds Long": {
              'IEF': listD6[10],
              'IGLT.L': listD6[11],
              'SYBB.DE': listD6[12],
              'Ire Long': listD6[13],
              'EUN3.DE': listD6[14],
              },
          "Property":{
              'Land Overall': listD6[15],
              'Land HMR': listD6[16],
              'Land': listD6[17],
              'Land Other': listD6[18],
              'Land UK': listD6[19],
          },
          "Deposits":{
              'Overnight_Ire': listD6[20],
              'ReedemableAtNotice': listD6[21],
              'Agreed Maturity < 2': listD6[22],
              'Agreed Maturity > 2': listD6[23],
          },
          "Business Wealth":{
              "Business Wealth S.E": listD6[24],
          }
          }}#,
      # houseName: {
      # "Equities": {
      #       '^GSPC': HNweights[0],
      #       '^FTSE': HNweights[1],
      #       '^STOXX': HNweights[2],
      #       '^IETP': HNweights[3],
      #       'IWDA.L': HNweights[4],
      #           },
      #     "Bonds Short": {
      #         # 'IB01.L': HNweights[5],
      #         'SHY': HNweights[5],
      #         'IGLS.L': HNweights[6],
      #         'SYB3.SW': HNweights[7],
      #         'Ire Short': HNweights[8],
      #         'IAGG': HNweights[9],
      #           },
      #     "Bonds Long": {
      #         'IEF': HNweights[10],
      #         'IGLT.L': HNweights[11],
      #         'SYBB.DE': HNweights[12],
      #         'Ire Long': HNweights[13],
      #         'EUN3.DE': HNweights[14],
      #         },
      #     "Property":{
      #         'Land Overall': HNweights[15],
      #         'Land HMR': HNweights[16],
      #         'Land': HNweights[17],
      #         'Land Other': HNweights[18],
      #         'Land UK': HNweights[19],
      #     },
      #     "Deposits":{
      #         'Overnight_Ire': HNweights[20],
      #         'ReedemableAtNotice': HNweights[21],
      #         'Agreed Maturity < 2': HNweights[22],
      #         'Agreed Maturity > 2': HNweights[23],
      #     },
      #     "Business Wealth":{
      #         "Business Wealth S.E": HNweights[24],
      #     }
      #     }}




      # "Template": {
      #     "Equities": {
      #       '^GSPC':
      #       '^FTSE':
      #       '^STOXX':
      #       '^IETP':
      #       'IWDA.L':
      #           },
      #     "Bonds Short": {
      #         'IB01.L':
      #         'IGLS.L':
      #         'SYB3.SW':
      #         'Ire Short':
      #         'IAGG':
      #           },
      #     "Bonds Long": {
      #         'IEF':
      #         'IGLT.L':
      #         'SYBB.DE':
      #         'Ire Long':
      #         'EUN3.DE':
      #         },
      #     "Property":{
      #         'Overall Ire'
      #         'Overall UK'
      #     },
      #     "Deposits":{
      #         'Overnight Ire':
      #         'Overnight UK':
      #         'Agreed Maturity Ire':
      #         'Agreed Maturity UK':
      #     }
      #     }

  housePriceLoc = "property_prices_data_RRPI.xlsx"
  # housePricePath = "/content/drive/MyDrive/Young_Economist" \
  housePricePath = data_dir / housePriceLoc
  if os.path.exists(housePricePath):
    if debug6 == True:
      print(f"WOOO {housePriceLoc} exists!")
  if not os.path.exists(housePricePath):
    raise FileNotFoundError(f"{housePriceLoc}.xlsx not found")
  df_house_prices = pd.read_excel(housePricePath)


  dataHMR = df_house_prices.iloc[5:, 1].astype(float)
  if debug6 == True:
    print(f"data for house prices, {dataHMR}")






  dataLand = df_house_prices.iloc[5:, 2].astype(float)
  if debug6 == True:
    print(f"data for house prices (non HMR), {dataLand}")


  if debug12 == True:
    print(f"data for house prices HMR: mean {np.nanmean(dataHMR)} std {np.nanstd(dataHMR)} [:50] {dataHMR[:50]}")
    print(f"data for house prices non HMR: mean {np.nanmean(dataLand)} np.nanstd {np.nanstd(dataLand)} [:50] {dataLand[:50]}")


  depositPricePath = data_dir / "CentralBankDepositData.xlsx" #"/content/drive/MyDrive/Young_Economist/CentralBankDepositData.xlsx" # from (B.1.1 CSV Central Bank retail intrest rates - deposits, outstanding amounts)
  if os.path.exists(depositPricePath):
    if debug6 == True:
      print("WOOO depositPricePath EXISTS. GOSH!!")
  if not os.path.exists(depositPricePath):
    raise FileNotFoundError("depositPricePath.xlsx not found")
  dfDepositPrices = pd.read_excel(depositPricePath)


  dataOvernight = dfDepositPrices.iloc[0:, 1].astype(float)
  dataReedemable = dfDepositPrices.iloc[0:, 2].astype(float)
  dataAgreedShort = dfDepositPrices.iloc[0:, 3].astype(float)
  dataAgreedLong = dfDepositPrices.iloc[0:, 4].astype(float)




  start = dt.datetime(2000, 1, 1)
  end = dt.datetime(2025, 1, 1)
  # time = []
  # for i in range((end - start).days):
    # time.append(start + dt.timedelta(days=i))
  extraTime = []
  for i in range((end - (start - dt.timedelta(days=1))).days):
    extraTime.append((start - dt.timedelta(days=1)) + dt.timedelta(days=i))

  time_dt = pd.bdate_range(start=start, end=end) # Business (252/yr)
  time = time_dt.to_pydatetime().tolist()


  debug = False
  optRun = False
  alpha = 0.15
    #===================================================================
  # CONFIGURATION
  #=================================================================== 

  

  structure = {
      "dict_arr_1": "dict of 1d arrays", 
      "dict_arr_2": "dict of 2d arrays", 
      "dict_s": "dict of scalars", 
      "df": "dataframe", 
      "l_dict_s": "list of dicts of scalars (prob. pairs)",
      "nest_dict_s": "nested_dict_of_scalars",
  }

  domain = {"ts": "time_series",
            "p": "mc_paths",
            "a": "aggregation"
  }
  
  metric_config = {
      "gap_results": {
          "target": "pairs",
          "structure": "dict_arr_1",
          "domain": "p",
          "metrics": ["mean", "med", "std", "p5", "p95", "len"]

      },
      "band_results": {
          "target": "coverage_raw",
          "structure": "nest_dict_s",
          "domain": "a",
          "metrics": ["mean", "med", "std", "len", "raw"]

      },
      "crps_results": {
          "target": "crps_scores",
          "structure": "dict_s",
          "domain": "a",
          "metrics": ["mean", "med", "std", "len", "raw"]

      },
      "convergence_results": {
          "target": "convergence_raw",
          "structure": "l_dict_s",
          "domain": "a",
          "metrics": ["std", "len", "raw"]

      },
      "back_test_results": {
          "target": "backtest_df",
          "structure": "df",
          "domain": "a",
          "metrics": ["mean", "med", "std", "raw"]

      },
      "house_cum_results": {
          "target": "plottingList",
          "structure": "dict_arr_1",
          "domain": "p",
          "metrics": ["mean", "med", "std", "p5", "p95", "len"]

      },
      "asset_vol_results": {
          "target": "sigmaDict",
          "structure": "dict_arr_1",
          "domain": "a",
          "metrics": ["mean", "med", "std", "p5", "p95"]

      },
      "house_vol_results": {
          "target": "house_vol_df",
          "structure": "df",
          "domain": "a",
          "metrics": ["raw"]

      },
      "mean_household_results": {
          "target": "meanPath",
          "structure": "dict_arr_1",
          "domain": "a",
          "metrics": ["terminal", "std", "raw"]

      },
    
      "name": {
          "target": "",
          "structure": "",
          "domain": "",
          "metrics": ["mean", "med", "std", "p5", "p95", "len", "raw", "terminal"]

      },
  }
  
  inputParameters = {
      "Overall": {
          "daysPerYear": 365,
          "useCholesky": False,
          "df_t": 5,
          "needed_graphs": 500

      },
      "Busniess Equity": {
          "busEpsScalar": 1.1,
          "alphaBusRaw": 0.035,

          "smallBlend": 0.4,
          "largeBlend": 0.6,

          "smallCapTicker": "IEUS",
          "largeCapTicker": '^125904-USD-STRD'
      },
      "Chunks": {
          "totalPaths": 5000,
          "chunkSize": 100,
      },
      "Correlation Modifier": {
        "Global Scalar": 1.0,
        "assetClassScalars": {
            "Business Equity": 1.0,
            "Deposits": 1.0,
            "Equities": 1.0,
            "Property": 1.0,
        },
        "Mode": "Global"
      },
      "percentile_bands": {
        '50% Band': {
            'high': 75,
            'low': 25
        },
        '80% Band': {
            'high': 90,
            'low': 10
        },
        '90% Band': {
            'high': 95,
            'low': 5,
        },
        '98% Band': {
            'high': 99,
            'low': 1,
        }

      },
      "asset_universe": {
        "Equities": {
            '^GSPC',
            '^FTSE',
            '^STOXX',
            '^IETP',
            'IWDA.L',
                },
        "Bonds Short": {
            'SHY',
            # 'IB01.L',
            'IGLS.L',
            'SYB3.SW',
            'IAGG',
              },
        "Bonds Long": {
            'IEF',
            'IGLT.L',
            'SYBB.DE',
            'EUN3.DE',
            },
        "Property":{
            'Land HMR',
            'Land Other',
        },
        "Deposits":{
            'Overnight_Ire',
            'ReedemableAtNotice',
            'Agreed Maturity < 2',
            'Agreed Maturity > 2'
        },
        "Business Wealth":{
            "Business Wealth S.E"
        }
          },
  }

  scenarios = [
    {
      "type": "returns",
      "name": "LowerReturns10",
      "muScalar": 0.9,
      "volScalar": 1.00,
      
    },
    {
        "type": "returns",
        "name": "HigherReturns10",
        "muScalar": 1.10,
        "volScalar": 1.00
    },
  
   {
    "type": "volatility",
    "name": "LowerVolatility10",
    "muScalar": 1.0,
    "volScalar": 0.90
   },
   {
      "type": "volatility",
      "name": "HigherVolatility10",
      "muScalar": 1.00,
      "volScalar": 1.10
   },
   {
      "type": "correlation",
      "name": "globalHigher5",
      "Global Scalar": 1.05,
      "Mode": "Global"
    },
    {
      "type": "correlation",
      "name": "globalLower5",
      "Global Scalar": 0.95,
      "Mode": "Global",
    },
    {
      "type": "correlation",
      "name": "globalHigher10",
      "Global Scalar": 1.10,
      "Mode": "Global",
    },
    {
      "type": "correlation",
      "name": "globalLower10",
      "Global Scalar": 0.90,
      "Mode": "Global"
    },
    {
      "type": "correlation",
      "name": "globalHigher20",
      "Global Scalar": 1.20,
      "Mode": "Global"
    },
    {
      "type": "correlation",
      "name": "globalLower20",
      "Global Scalar":0.80,
      "Mode": "Global"
    },
    {
       "type": "df_t",
       "name": "df3",
       "df_t": 3,

    },
    {
       "type": "df_t",
       "name": "df8",
       "df_t": 8,

    },
    {
       "type": "df_t",
       "name": "df15",
       "df_t": 15,

    },
    {
       "type": "df_t",
       "name": "df30",
       "df_t": 30,

    },
    {
       "type": "df_t",
       "name": "df1000",
       "df_t": 1000,

    },
    {
    "type": "business_wealth",
    "name": "SmallCapHeavy",
    "smallBlend": 0.75,
    "largeBlend": 0.25
    },

    {
      "type": "business_wealth",
      "name": "LargeCapHeavy",
      "smallBlend": 0.25,
      "largeBlend": 0.75
    },
    {
    "type": "business_wealth",
    "name": "alphaBus3%",
    "alphaBusRaw": 0.03
    },

    {
    "type": "business_wealth",
    "name": "alphaBus4%",
    "alphaBusRaw": 0.04
    },
    

    {
      "type": "business_wealth",
      "name": "BusEps1.2",
      "busEpsScalar": 1.2
    },

    {
      "type": "business_wealth",
      "name": "BusEps1",
      "busEpsScalar": 1
    },
    {
      "type": "business_wealth",
      "name": "BusEps0.8",
      "busEpsScalar": 0.8
    },

    {
      "type": "business_wealth",
      "name": "BusEps1.4",
      "busEpsScalar": 1.4
    }
    
  ]


  assets = {
        "Equities": {
          '^GSPC',
          '^FTSE',
          '^STOXX',
          '^IETP',
          '^990100-USD-STRD', # MSCI WORLD # was IWDA.L but not enough time
              },
        "Bonds Short": {
            'SHY',
            # 'IB01.L',
            'IGLS.L',
            'SYB3.SW',
            'Ire Short',
            'IAGG',
              },
        "Bonds Long": {
            'IEF',
            'IGLT.L',
            'SYBB.DE',
            'Ire Long',
            'EUN3.DE',
            },
        "Property":{
            'Land Overall',
            'Land HMR',
            'Land',
            'Land Other',
            'Land UK',
        },
        "Deposits":{
            'Overnight_Ire',
            'ReedemableAtNotice',
            'Agreed Maturity < 2',
            'Agreed Maturity > 2'
        },
        "Business Wealth":{
            "Business Wealth S.E"
        }
}


  assetsYahoo = {
          "Equities": {
            '^GSPC',
            '^FTSE',
            '^STOXX',
            '^IETP',
            '^990100-USD-STRD', # MSCI WORLD # was IWDA.L but not enough time
                },
          "Bonds Short": {
              # 'IB01.L',
              'SHY',
              'IGLS.L',
              'SYB3.SW',
              'IAGG',
                },
          "Bonds Long": {
              'IEF',
              'IGLT.L',
              'SYBB.DE',
              'EUN3.DE',
              }
              }
  assetsCompleted = {
              "Equities": {
            '^GSPC',
            '^FTSE',
            '^STOXX',
            '^IETP',
            '^990100-USD-STRD', # MSCI WORLD # was IWDA.L but not enough time
                },
          "Bonds Short": {
              'SHY',
              # 'IB01.L',
              'IGLS.L',
              'SYB3.SW',
              'IAGG',
                },
          "Bonds Long": {
              'IEF',
              'IGLT.L',
              'SYBB.DE',
              'EUN3.DE',
              },
          "Property":{
              'Land HMR',
              'Land Other',
          },
          "Deposits":{
              'Overnight_Ire',
              'ReedemableAtNotice',
              'Agreed Maturity < 2',
              'Agreed Maturity > 2'
          },
          "Business Wealth":{
              "Business Wealth S.E"
          }
          }




  corrAbleClasses = ["Equities", "Bonds Short", "Bonds Long", 'Business Wealth']#, 'Property', 'Deposits']
  # return {
  #   "assetWeights": assetWeights,
  #   "metric_config": metric_config,
  #   "chunk_dir": chunk_dir,
  #   "graph_dir": graph_dir,
    
  # }
  return {
      "assetsCompleted": assetsCompleted, 
      "assetsYahoo":assetsYahoo, 
      "assets":assets, 
      "assetWeights":assetWeights, 
      "households": households, 
      "time": time, 
      "folder": folder,
      "chunkFolder": chunkFolder, 
      # "fullSavedAssetRes": fullSavedAssetRes, 
      "corrAbleClasses": corrAbleClasses, 
      "metric_config": metric_config, 
      "chunk_dir": chunk_dir, 
      "graph_dir":graph_dir, 
      "data_dir": data_dir, 
      "scenarios": scenarios, 
      "inputParameters": inputParameters}

  # setup: takes (), returns: assetsCompleted, assetsYahoo, assets, assetWeights, households, time, folder, chunkFolder

        # _--------------------------------------------------------------------------------------------------------------------------------------
        #                               ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ running ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # _--------------------------------------------------------------------------------------------------------------------------------------
import subprocess
def backup_file(filename):
   pass
#     subprocess.run([
#         "rclone",
#         "copy",
#         filename,
#         "gdrive:Young_Economist/chunkResults"
#     ], check=True)

def _save_item(item, path=None, base_path=None, add_to_base=None):
      if path == None and base_path == None and add_to_base == None:
        print(f"Everything was none. Notice_me!")
        return None

      elif path == None and base_path != None and add_to_base != None:
         path = os.path.join(base_path, add_to_base)
      elif path != None:
         path = path
      else:
        print(f"Something was none. Notice_me!")
        return None

      os.makedirs(os.path.dirname(path), exist_ok=True)
      try:
          try:
              with zstd.open(path, "wb") as f:
                  pickle.dump(item, f)
          except zstd.ZstdError:
              with open(path, "wb") as f:
                pickle.dump(item, f)
      except Exception as e:
          print("Failed to save item:", e)
          return None
      backup_file(path)
      print("Saved item:", path)
def aggregate_to_asset_paths(nTotalPaths, V_num, statePath=None, resultPath=None):

  stage = "asset_agg"
  faield_count = 0

  def _saveAssetState(state, path):

      os.makedirs(os.path.dirname(path), exist_ok=True)
      try:
        with open(path, "wb") as f:
            pickle.dump(state, f)
      except Exception as e:
          print("Failed to load asset state:", e)
          return None
      backup_file(path)
      print("Saved asset state:", path)


  def _loadAssetState(path):

      if not os.path.exists(path):
          print("No previous asset state.")
          return None

      try:
          try:
              with zstd.open(path, "rb") as f:
                  state = pickle.load(f)
          except zstd.ZstdError:
             with open(path, "rb") as f:
                  state = pickle.load(f)

          print("Loaded asset state with", state["pathCounter"], "paths")
          return state

      except Exception as e:
          print("Failed to load asset state:", e)
          return None

  def streamingAssetAggregator(
      all_files,
      assetWeights,
      chunkFolder,
      nTotalPaths,
      statePath,
      resultPath,
      debug=False
  ):

      state = _loadAssetState(statePath)

      if state is None:

          meanAssetPath = {}
          M2AssetPath = {}
          sampleAssetPaths = {}

          meanAssetClassPath = {}
          M2AssetClassPath = {}
          sampleAssetClassPaths = {}

          processedFiles = set()
          pathCounter = 0

      else:
          print(statePath)
          # print(state.items())
          meanAssetPath = state["meanAssetPath"]
          M2AssetPath = state["M2AssetPath"]
          sampleAssetPaths = state["sampleAssetPaths"]

          meanAssetClassPath = state["meanAssetClassPath"]
          M2AssetClassPath = state["M2AssetClassPath"]
          sampleAssetClassPaths = state["sampleAssetClassPaths"]

          processedFiles = state["processedFiles"]
          pathCounter = state["pathCounter"]

      # -------------------------------------------------

      for fname in all_files:

          if fname in processedFiles:
              continue

          filePath = os.path.join(chunkFolder, fname)
          print(f"file path {filePath}")
          try:
              try:
                  with zstd.open(filePath, "rb") as f:
                      chunk = pickle.load(f)
              except zstd.ZstdError:
                  with open(filePath, "rb") as f:
                      chunk = pickle.load(f)

              mcData = chunk["chunkResults"]["monteCarlo"]

              assetReturnPathsList = mcData["allAssetReturnPaths"]

          except Exception as e:
              print("Failed loading", fname, e)
              continue

          print("Processing", fname)

          # -------------------------------------------------

          for assetReturnPaths in assetReturnPathsList:

              if pathCounter >= nTotalPaths:
                  break

              pathCounter += 1

              households = list(assetReturnPaths.keys())

              for assetClass in assetReturnPaths[households[0]]:

                  tickers = assetReturnPaths[households[0]][assetClass].keys()

                  tickerReturns = []

                  for ticker in tickers:

                      hPaths = []

                      for h in households:

                          weighted_r = np.array(
                              assetReturnPaths[h][assetClass][ticker]
                          )

                          weight = assetWeights[h][assetClass][ticker]

                          if weight == 0:
                              continue

                          # recover underlying return
                          r = weighted_r / weight

                          hPaths.append(r)

                      if len(hPaths) == 0:
                          continue

                      r = np.nanmean(np.stack(hPaths), axis=0)

                      if debug and pathCounter < 5:
                          print(
                              "DEBUG asset:",
                              assetClass,
                              ticker,
                              "mean weighted:",
                              np.nanmean(weighted_r),
                              "mean recovered:",
                              np.nanmean(r)
                          )

                      # -----------------------------------------
                      # initialise asset structures
                      # -----------------------------------------

                      if assetClass not in meanAssetPath:

                          meanAssetPath[assetClass] = {}
                          M2AssetPath[assetClass] = {}
                          sampleAssetPaths[assetClass] = {}

                      if ticker not in meanAssetPath[assetClass]:

                          meanAssetPath[assetClass][ticker] = np.zeros_like(r)
                          M2AssetPath[assetClass][ticker] = np.zeros_like(r)
                          sampleAssetPaths[assetClass][ticker] = []

                      if len(sampleAssetPaths[assetClass][ticker]) < 300:

                          sampleAssetPaths[assetClass][ticker].append(r.copy())

                      # -----------------------------------------
                      # Welford update
                      # -----------------------------------------

                      delta = r - meanAssetPath[assetClass][ticker]

                      meanAssetPath[assetClass][ticker] += delta / pathCounter

                      M2AssetPath[assetClass][ticker] += delta * (
                          r - meanAssetPath[assetClass][ticker]
                      )

                      tickerReturns.append(r)

                  # -----------------------------------------
                  # Asset class aggregation
                  # -----------------------------------------

                  if len(tickerReturns) == 0:
                      continue

                  classReturn = np.nanmean(np.stack(tickerReturns), axis=0)

                  if assetClass not in meanAssetClassPath:

                      meanAssetClassPath[assetClass] = np.zeros_like(classReturn)
                      M2AssetClassPath[assetClass] = np.zeros_like(classReturn)
                      sampleAssetClassPaths[assetClass] = []

                  if len(sampleAssetClassPaths[assetClass]) < 300:

                      sampleAssetClassPaths[assetClass].append(classReturn.copy())

                  delta = classReturn - meanAssetClassPath[assetClass]

                  meanAssetClassPath[assetClass] += delta / pathCounter

                  M2AssetClassPath[assetClass] += delta * (
                      classReturn - meanAssetClassPath[assetClass]
                  )

          processedFiles.add(fname)

          # -------------------------------------------------
          # save progress
          # -------------------------------------------------

          state = {

              "meanAssetPath": meanAssetPath,
              "M2AssetPath": M2AssetPath,
              "sampleAssetPaths": sampleAssetPaths,

              "meanAssetClassPath": meanAssetClassPath,
              "M2AssetClassPath": M2AssetClassPath,
              "sampleAssetClassPaths": sampleAssetClassPaths,

              "processedFiles": processedFiles,
              "pathCounter": pathCounter
          }

          _saveAssetState(state, statePath)

          if pathCounter >= nTotalPaths:
              break
          del chunk, mcData, assetReturnPathsList
          
          gc.collect()
      # -------------------------------------------------
      # compute sigma
      # -------------------------------------------------

      sigmaAssetPath = {}
      divisor = pathCounter - 1 if pathCounter > 1 else 1
      for c in meanAssetPath:

          sigmaAssetPath[c] = {}

          for t in meanAssetPath[c]:

              sigmaAssetPath[c][t] = np.sqrt(
                  M2AssetPath[c][t] / (divisor)
              )

      sigmaAssetClassPath = {}

      for c in meanAssetClassPath:

          sigmaAssetClassPath[c] = np.sqrt(
              M2AssetClassPath[c] / divisor
          )

      result = {

          "sampleAssetPaths": sampleAssetPaths,
          "meanAssetPath": meanAssetPath,
          "sigmaAssetPath": sigmaAssetPath,

          "sampleAssetClassPaths": sampleAssetClassPaths,
          "meanAssetClassPath": meanAssetClassPath,
          "sigmaAssetClassPath": sigmaAssetClassPath,

          "pathCounter": pathCounter
      }

      _saveAssetState(result, resultPath)

      print("Asset aggregation complete.")

      return result

  chunkFolder = chunk_dir #"/content/drive/MyDrive/Young_Economist/chunkResults"
  # from google.colab import drive
  # drive.mount('/content/drive')

  os.makedirs(chunkFolder, exist_ok=True)
  if not os.path.exists(chunkFolder):
      print(f"Error: The folder '{chunkFolder}' does not exist. Please ensure Google Drive is mounted and the path is correct.")
      raise FileNotFoundError(f"Directory not found: {chunkFolder}")

  all_files = [f for f in os.listdir(chunkFolder) if f.startswith("Chunk_Results_") and f.endswith(".pkl") and f"{V_num}" in f]

  def extract_start_index(fname):
      parts = fname.replace(".pkl", "").split("_")
      return int(parts[-2])

  all_files.sort(key=extract_start_index)

  # partial_results = []

  count = 0
  for fname in all_files:
      if count == 0:
        filePath = os.path.join(chunkFolder, fname)
        try:
            try:
                with zstd.open(filePath, "rb") as f:
                    chunkData = pickle.load(f)
                    # partial_results.append(chunkData)
                    count += 1
                    print(f"Loaded {fname}, chunk index = {chunkData['chunkIndex']}")
            except zstd.ZstdError:
                with open(filePath, "rb") as f:
                    chunkData = pickle.load(f)
                    # partial_results.append(chunkData)
                    count += 1
                    print(f"Loaded {fname}, chunk index = {chunkData['chunkIndex']}")
            inputs = chunkData['chunkResults']['inputs']
            del chunkData
            gc.collect() # Force clear RAM
            
        except Exception as e:
            print(f"Failed to load {fname}: {e}")


  time = pd.to_datetime(inputs['time'])
  xAxisDates = pd.to_datetime(time)
  assetWeights = inputs['assetWeights']
  assetStatePath = statePath if statePath else data_dir / f"assetState_{V_num}.pkl"
  resultPath = resultPath if resultPath else data_dir / f"assetStateResults_{V_num}.pkl"

  assetResults = streamingAssetAggregator(
      all_files,
      assetWeights,
      chunkFolder,
      nTotalPaths= nTotalPaths,
      statePath=assetStatePath,
      resultPath = resultPath,
      debug=False
  )
  if debugAggregation:
      for c in assetResults["meanAssetPath"]:
          for t in assetResults["meanAssetPath"][c]:
              print(
                  c,
                  t,
                  np.nanmean(assetResults["meanAssetPath"][c][t])
              )
  return assetResults








# print(fullSavedAssetRes['meanAssetPath'])
def portfolioAggregation(assetWeights, fullSavedAssetRes, households, assetsCompleted):
  stage = "port_agg"
  failed_count = 0 

  returnExample = fullSavedAssetRes['meanAssetPath']['Business Wealth']['Business Wealth S.E']
  portRet = {h: np.zeros_like(returnExample) for h in households}
  portCumR = {h: np.zeros_like(returnExample) for h in households}
  portAssetRet = {h: {} for h in households}
  portAssetCumR = {h: {} for h in households}
  weightTotal = {h: 0 for h in households}
  portSigma = {h: np.zeros_like(returnExample) for h in households}
  portSigmaSquare = {h: np.zeros_like(returnExample) for h in households}
  portSamplePaths = {h: [] for h in households}
  portSampleCum = {h: [] for h in households}
  portSampleSigmaSquare = {h: [] for h in households}
  portSampleSigma = {h: [] for h in households}
  assetToClass = {}
  for className in assetsCompleted:
    for asset in assetsCompleted[className]:
      assetToClass[asset] = className


  # initilised


  for h in households:
    weightTotal[h] = 0
    for assetClass in assetsCompleted:
      if debugAggregation:
        print(f"assetClass = {assetClass}")
      portAssetRet[h][assetClass] = {}
      portAssetCumR[h][assetClass] = {}
      for asset in assetsCompleted[assetClass]:
        portAssetRet[h][assetClass][asset] = np.zeros_like(returnExample)
        portAssetCumR[h][assetClass][asset] = np.zeros_like(returnExample)
    for assetClass in fullSavedAssetRes['meanAssetPath']:
      for asset in fullSavedAssetRes['meanAssetPath'][assetClass]:
        if debugAggregation:
          print(f"asset {asset}")




        ret = fullSavedAssetRes['meanAssetPath'][assetClass][asset]
        # print(f"WOOO MEAN SHAPE {asset} {ret.shape}")
        sigma = fullSavedAssetRes['sigmaAssetPath'][assetClass][asset]
        samples = fullSavedAssetRes['sampleAssetPaths'][assetClass][asset]
        portAssetWeight = assetWeights[h][assetClass][asset]
        # sample_sigmas = fullSavedAssetRes['sampleAssetSigmas'][assetClass][asset]

        nSamples = len(samples)


        for i in range(nSamples):
          if len(portSamplePaths[h]) <= i:
            portSamplePaths[h].append(np.zeros_like(samples[i]))  # match sample shape
          portSamplePaths[h][i] += samples[i] * portAssetWeight

          # if len(portSampleSigmaSquare[h]) <= i:
          #   portSampleSigmaSquare[h].append(np.zeros_like(sample_sigmas[i]))
          # portSampleSigmaSquare[h][i] += (portAssetWeight ** 2) * (sample_sigmas[i] ** 2)  

        weightTotal[h] += portAssetWeight
        # print(f"weightTotal {h} {weightTotal}")
        portAssetRetNew = ret * portAssetWeight
        # portAssetCumNew = np.cumprod(1 + portAssetRetNew) - 1
        portAssetRet[h][assetClass][asset] = portAssetRetNew
        # portAssetCumR[h][assetClass][asset] = portAssetCumNew
        portRet[h] += portAssetRetNew
        # portSigmaSquare[h] += (portAssetWeight ** 2) * (sigma ** 2)
        # portCumR[h] += portAssetCumNew
        if debugAggregation:
          print(f"{h} {np.nanmean(portRet[h])}")
      # print(household)
    portCumR[h] = np.cumprod(1 + portRet[h]) - 1
    # portSigma[h] = np.sqrt(portSigmaSquare[h])
    if debugAggregation:
      print(f"Cum R {h} {portCumR[h][-1]}")
    for returnSeries in portSamplePaths[h]:
      portSampleCum[h].append(np.cumprod(1 + returnSeries) - 1)
    # for var_path in portSampleSigmaSquare[h]:
    #         portSampleSigma[h].append(np.sqrt(var_path))
    #

  # NOTE: this used to be nested INSIDE the "for h in households:" loop above,
  # with its own "for h in households:" reusing the same loop variable "h".
  # That meant portSigma was recomputed redundantly on every outer pass (9
  # total passes for 3 households instead of 3), appending duplicate entries
  # into portSampleSigma[h] each time. It did not swap household identities
  # (each h's portSigma only ever read portSamplePaths[h]), but it was wasteful
  # and fragile. Moved out to its own loop, run once, after every household's
  # portSamplePaths is fully built.
  vol_window = 21  # 21 trading days (~1 month) rolling window

  for h in households:
    for returnSeries in portSamplePaths[h]:
        # Compute rolling standard deviation path, handling the initial window gap smoothly
        rolling_vol = pd.Series(returnSeries).rolling(window=vol_window, min_periods=1).std().to_numpy(copy=True)
        rolling_vol[:vol_window] = rolling_vol[vol_window]
        # Backfill the first 20 days of NaN values with the first valid volatility
        # valid_idx = pd.Series(rolling_vol).first_valid_index()
        # if valid_idx is not None:
        #     rolling_vol[:valid_idx] = rolling_vol[valid_idx]
        # else:
        #     rolling_vol = np.zeros_like(rolling_vol)
        portSampleSigma[h].append(rolling_vol)
    portSigma[h] = np.nanmean(portSampleSigma[h], axis=0)
  summaryRows = []


  for h in households:
      summaryRows.append({
          "Household": h,
          "Mean Cumulative Return": portCumR[h][-1],
          "Mean Std Daily Return": np.nanmean(portSigma[h]),
          "Mean Daily Return": np.nanmean(portRet[h]),
          # "Lifetime Return (80)": np.cumprod(1 + )
      })
      summaryTable = pd.DataFrame(summaryRows)
  aggRes = {
      "portCumR": portCumR,
      "portSigma": portSigma,
      "portSamplePaths": portSamplePaths,
      "portRet": portRet,
      "portSampleCum": portSampleCum,
      "portSampleSigma": portSampleSigma,
      "summaryTable": summaryTable,
      "portAssetRet": portAssetRet

  }
  return aggRes
# aggRes = portfolioAggregation(assetWeights)





def getOgAssetClassWeights(assetWeights):
  assetClassOgWeights = {h: {} for h in households}
  for h in assetWeights:
    for assetClass in assetWeights[h]:
      assetClassOgWeights[h][assetClass] = 0
      for ticker in assetWeights[h][assetClass]:
        tickerValue = assetWeights[h][assetClass][ticker]
        assetClassOgWeights[h][assetClass] += tickerValue


      print(f"{h} {assetClass} {assetClassOgWeights[h][assetClass]}")


    sum = 0
    for assetClass in assetClassOgWeights[h]:
      value = assetClassOgWeights[h][assetClass]
      sum += value
    print(f"WOO SUM IS {h} {sum}")
  return assetClassOgWeights
# assetClassOgWeights = getOgAssetClassWeights(assetWeights)
# print(assetClassOgWeights)
# assetWeightsOG = assetWeights



@njit
def _garch_loop(z, mu, omega, alpha1, beta1, beta2, first_sigma, first_eps):

    # JIT-compiled GARCH(1,2) simulation loop.
    # Returns r, sigma, p arrays each of length len(z)-2.

    n = len(z)
    # pre-allocate output arrays
    r_out     = np.empty(n)
    sigma_out = np.empty(n)
    eps_out   = np.empty(n)
    # p_out     = np.empty(n - 2)

    sigma_out[0] = first_sigma
    sigma_out[1] = first_sigma
    eps_out[0]   = first_eps
    eps_out[1]   = first_eps
    r_out[0]     = mu + first_eps
    r_out[1]     = mu + first_eps
    # p_prev       = 1.0  # placeholder

    for t in range(2, n):
        new_sigma = (omega
                    + alpha1 * eps_out[t-1]**2
                    + beta1  * sigma_out[t-1]**2
                    + beta2  * sigma_out[t-2]**2) ** 0.5
        if new_sigma > 0.10: # caps volatility to prevent alpha + beta being > 1
            new_sigma = 0.10
        sigma_out[t] = new_sigma
        new_eps      = new_sigma * z[t]
        eps_out[t]   = new_eps
        new_r        = mu + new_eps
        r_out[t]   = new_r
        
    # maxDaily = 3
    # maxAllowed = maxDaily # 1000,000
    # object_searched = r_out
    # maxFound = get_absolute_max(object_searched)
    # location = find_value_location(object_searched, maxFound)
    # assert maxFound < maxAllowed, (
    # f"Error: returns have exploded. Max found {maxFound}, {h}, {location} in _garch_loop"
    # )
    return r_out, sigma_out, eps_out
  


debugADC = False
# =================================================================================================================================
#
# ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    =====
# ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    =====


# =================================================================================================================================
# runGraphs(aggRes)


import ipywidgets as widgets
from IPython.display import display, clear_output
def getGraphs(assetRes):
  # assetRes = x
  assetClassColours = {
      "Equities": "tab:red",
      "Bonds Short": "tab:blue",
      "Bonds Long": "tab:purple",
      "Property": "tab:orange",
      "Deposits": "tab:green",
      "Business Wealth": "#FFD700"
  # "Equities", "Bonds Short": "tab:blue", "Bonds Long": "tab:purple", "Property": "tab:orange", "Deposits"
  }
  houseHoldAssetsColours = {
      "80-100": "tab:red",
      "0-20": "tab:blue",
      "40-59": "tab:green"
  }
  # for path in mc["samplePathsPortCumR"]:
  #   for household in path:
  #     # plt.plot(x, path[household], label=f"Household {household}")
  #     key = x, path[household], label=f"Household {household}"
  #     keyList.append(key)
  #     print(f"(Graphing) path is {path}, household is {household}, path[household] is {path[household]} ")
  # for path in mc["samplePathsPortCumR"]










  plt.rcParams.update({
      'font.size': 20,
      'axes.titlesize': 25,
  #title
      'axes.labelsize': 24,
      'xtick.labelsize': 20,
      'ytick.labelsize': 20,
      'legend.fontsize': 20,
      'figure.titlesize': 20
  })
  householdDisplayLabels = {
      "0-20": "0–20th Income Percentile",
      "40-59": "40–59th Income Percentile",
      "80-100": "80–100th Income Percentile"
  }


  x = pd.to_datetime(time)
  plottingList = {}
  currentPath = []
  currentHousehold = []


  # for path in mc["sampleHouseholdCum"]:
  #   for household in path:
  #     print(f"Household == {household}")
  #     plottingList[household] = {}


  plottingList = {
      '80-100': [],
      '40-59': [],
      '0-20': []
  }
  minValue = {
      '80-100': 0,
      '40-59': 0,
      '0-20': 0
  }
  maxValue = {
      '80-100': 0,
      '40-59': 0,
      '0-20': 0
  }
  minList = {
      '80-100': [],
      '40-59': [],
      '0-20': []
  }
  maxList = {
      '80-100': [],
      '40-59': [],
      '0-20': []
  }


  houseHoldAssetsColours = {
      "80-100": "tab:red",
      "0-20": "blue",
      "40-59": "tab:green"
  }
  houseHoldAssetsColoursIntense = {
      "80-100": "deeppink",
      "0-20": "c",
      "40-59": "lime"
  }
  assetClassColours = {
      "Equities": "tab:red",
      "Bonds Short": "tab:blue",
      "Bonds Long": "tab:purple",
      "Property": "tab:orange",
      "Deposits": "tab:green",
      "Business Wealth": "#FFD700"
  # "Equities", "Bonds Short": "tab:blue", "Bonds Long": "tab:purple", "Property": "tab:orange", "Deposits"
  }


    # ================================================================================
  graphFigSize = (14,6)
  alpha = 0.2
  def houseCumSampleWithSigmaBanded():
    x = pd.to_datetime(time)
    plt.figure(figsize=graphFigSize)
    for h in households:
      upper = (assetRes['portCumR'][h] + assetRes['portSigma'][h])*100
      lower = (assetRes['portCumR'][h] - assetRes['portSigma'][h])*100
      plt.fill_between(x, lower, upper, color=houseHoldAssetsColoursIntense[h], alpha=1)
      plt.plot(x, upper, color=houseHoldAssetsColoursIntense[h], alpha=1, linewidth=4, linestyle='--')
      plt.plot(x, lower, color=houseHoldAssetsColoursIntense[h], alpha=1, linewidth=4, linestyle='--')
      for path in assetRes['portSampleCum'][h]:
        plt.plot(x, path*100, color=houseHoldAssetsColours[h], alpha=alpha, linewidth=0.8)
      # mean
      # plt.plot(x, assetRes['portCumR'][h]*100, color=houseHoldAssetsColoursIntense[h], label=householdDisplayLabels[h], linewidth=4)


      # sigma bands +/- 1, why not


    plt.title("Household Portfolio: Sample Cumulative Return with Volatility Bands")
    plt.xlabel("Date")
    plt.ylabel("Cumulative Return (%)")
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title="HH Income Group")
    plt.show()


  def householdCumVolatility():
    x = pd.to_datetime(time)
    plt.figure(figsize=(14,6))
    for h in households:
      plt.plot(x, mc['stdHouseholdCum'][h], label=f"{h} Household Volatility", color=houseHoldAssetsColours[h])
    plt.title("Household Cumulative Volatility Over Time")
    plt.xlabel("Time")
    plt.ylabel("Volatility")
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
    plt.legend(
          loc="upper right",
          fontsize=15,          # smaller font (half if original was ~12)
          title_fontsize=17,    # smaller title
          handlelength=1.5,      # shorter legend lines
          handleheight=1,    # shrink vertical size of handles
          labelspacing=.6     # reduce vertical spacing between labels
      )
    plt.grid(True)
    plt.show()
  # running graphs proper
  houseCumSampleWithSigmaBanded()
# ============================================================================================================================================================================


# ============================================================================================================================================================================
#initalising
# userWeights = {h: {ac: {t: 0.0 for t in assetsCompleted[ac]} for ac in assetsCompleted} for h in households}
# userWeights = assetWeightsOG
# userClassWeights = assetClassOgWeights


# userClassWeights = {h: {ac: 0.0 for ac in assetsCompleted} for h in households}
# userWeights = assetWeights


def interactPortInterface():
  output = widgets.Output()


  #house select
  householdSelector = widgets.Dropdown(
      options=households,
      value=households[0],
      description="Household:"
  )


  assetClassSelector = widgets.Dropdown(
      options= list(assetsCompleted.keys()),
      value= list(assetsCompleted.keys())[0],
      description = 'Asset Category:'
  )


  # tickerSliders = widgets.VBox()


  assetClassSliders = []
  for assetClass in assetsCompleted:
    slider = widgets.FloatSlider(
        value = userClassWeights[householdSelector.value][assetClass],
        min=0,
        max=1,
        step=0.01,
        description = assetClass,
        readout_format = '.2f'
      )
    assetClassSliders.append(slider)
  slidersBox = widgets.VBox(assetClassSliders)


  def updateSliders(change):
    h = householdSelector.value
    for slider in assetClassSliders:
      slider.value = userClassWeights[h][slider.description]
    # tickerSliders.children = sliders
  householdSelector.observe(updateSliders, names='value')
  # updateTickers(None)


  bigRedButton = widgets.Button(description='Simulate Portfolio')


  def onButtonPress(button):
    h = householdSelector.value
    for slider in assetClassSliders:
      userClassWeights[h][slider.description] = slider.value


    # map to ticker weights
    for assetClass in assetsCompleted:
      tickers = assetsCompleted[assetClass]
      # OG ticker level weights
      classOGWeights = np.array([
          assetWeights[h][assetClass][t] for t in tickers
      ])
      if classOGWeights.sum() > 0:
        classOGWeights /= classOGWeights.sum()
      else:
        classOGWeights = np.ones_like(classOGWeights) / len(classOGWeights)
      for i, t in enumerate(tickers):
        userWeights[h][assetClass][t] = userClassWeights[h][assetClass] * classOGWeights[i]


    # assetClass = assetClassSelector.value
    # for slider in tickerSliders.children:
    #   userWeights[h][assetClass][slider.description] = slider.value
    # print(userWeights)
    # =============================================================
    # getting assetWeights
    # ============================================================


    aggRes = portfolioAggregation(userWeights)


    clear_output(wait=True)
    print(userWeights)
    print(f"Results:")
    runGraphs(aggRes)




  bigRedButton.on_click(onButtonPress)
#   display(householdSelector, slidersBox, bigRedButton)


# interactPortInterface()


#=============================================================================================================================================


    #                     Interactive local =============================================================================================================================================
    # =============================================================================================================================================
    # =============================================================================================================================================


    # =============================================================================================================================================


# tqdm.tqdm = lambda *args, **kwargs: None


# !pip install arch
# import arch
import matplotlib.pyplot as plt
import matplotlib
# !pip install scipy
from scipy.optimize import minimize
from scipy.stats import t as studentT
# !pip install warnings
# !pip install arch.utility
# import warnings
# from arch.utility.exceptions import DataScaleWarning
# warnings.simplefilter("ignore", DataScaleWarning)
# warnings.simplefilter("ignore", FutureWarning)
# import numpy as np

# import os
# os.environ["TQDM_DISABLE"] = "1"
debug2 = False
debug3 = False
debug4 = False # z
debug5 = False #minimal
debug6 = False #start up
debug7 = False
debug8 = False #(first Eps, etc)
debug9 = False # property stuff for r
debug10 = False # alpha, beta, etc
debug11 = False
debug12 = False
debugBus = False
debug14 = False
debugVolatility3 = False
debugAggregation = False
import pickle
alreadyRun = 12
daysPerYear = 365


if alreadyRun != 1:
  import matplotlib.cm as cm
  import os
  import tqdm
  tqdm.tqdm = lambda *args, **kwargs: None
  # !pip install pandas_datareader.data
  # !pip install yfinance
  import yfinance as yf
  # yf.tqdm.tqdm = lambda *args, **kwargs: args[0] if args else None
  # yf.utils.disable_progress_bar()


  # !pip install arch
  # !pip install numpy
  # !pip install matplotlib


  # !pip install warnings
  # !pip install arch.utility
  import arch
  import warnings
  from arch.utility.exceptions import DataScaleWarning
  from arch.utility.exceptions import ConvergenceWarning
  warnings.simplefilter("ignore", DataScaleWarning)
  warnings.simplefilter("ignore", FutureWarning)
  warnings.simplefilter("ignore", ConvergenceWarning)
  from tqdm.auto import tqdm
  tqdm.__init__ = lambda *args, **kwargs: None


  import matplotlib.pyplot as plt
  import os
  os.environ["TQDM_DISABLE"] = "1"


  import numpy as np
  print(arch.__version__)


  import datetime as dt


  import pandas as pd
#   from google.colab import files
  # import pandas_datareader.data as web
  from arch import arch_model




import io # Import the io module


# if 10 == 1:


#   uploaded = files.upload()


#   for fn in uploaded.keys():
#     # Read the excel file directly from the bytes content
#     df = pd.read_excel(io.BytesIO(uploaded[fn]))
#     if debug6 == True:
#      print(df)
#     break # Exit loop after processing the first file


# from google.colab import drive
# drive.mount('/content/drive')




# assets = {
#     "Equities": {
#         '^GSPC': '^GSPC',
#         '^STOXX': '^STOXX',
#         '^IETP': '^IETP'
#         },
#     #S and P, Eur Stoxx 600, Irish 20
#     "Bonds" : {'AGG': 'AGG',
#                'SPFF.DE': 'SPFF.DE',
#                'SYB4.DE': 'SYB4.DE'},d
#     # US, Global (not Corp differnciated + Eur Based), and Eur-Area
#     "Deposit": {
#      "Deposit": "Deposit"
#     }


#     }


classWeightsHousehold = {
    "Equities": 0.33,
    "Bonds": 0.24,
    "Deposit": .43
}


assetWeightsHousehold = {


    "Equities": {
        '^GSPC': 0.5,
        '^STOXX': 0.3,
        '^IETP': 0.2
        },
    #S and P, Eur Stoxx 600, Irish 20
    "Bonds" : {'AGG': 0.5,
               'SPFF.DE': 0.3,
               'SYB4.DE': 0.2
        },
    # US, Global (not Corp differnciated + Eur Based), and Eur-Area
    "Deposit": {
     "Deposit": 1.0
    }
}




households = ["80-100", "40-59", "0-20"]
# assetClass = ["Equities", "Bonds Short", "Bonds Long", "Property", "Deposits"]


# assetWeights = {
#     "80-100": {
#         "Equities": {
#           '^GSPC': listD10[0],
#           '^FTSE': listD10[1],
#           '^STOXX': listD10[2],
#           '^IETP': listD10[3],
#           'IWDA.L': listD10[4],
#               },
#         "Bonds Short": {
#             # 'IB01.L': listD10[5],
#             'SHY': listD10[5],
#             'IGLS.L': listD10[6],
#             'SYB3.SW': listD10[7],
#             'Ire Short': listD10[8],
#             'IAGG': listD10[9],
#               },
#         "Bonds Long": {
#             'IEF': listD10[10],
#             'IGLT.L': listD10[11],
#             'SYBB.DE': listD10[12],
#             'Ire Long': listD10[13],
#             'EUN3.DE': listD10[14],
#             },
#         "Property":{
#             'Land Overall': listD10[15],
#             'Land HMR': listD10[16],
#             'Land': listD10[17],
#             'Land Other': listD10[18],
#             'Land UK': listD10[19],
#         },
#         "Deposits":{
#             'Overnight_Ire': listD10[20],
#             'ReedemableAtNotice': listD10[21],
#             'Agreed Maturity < 2': listD10[22],
#             'Agreed Maturity > 2': listD10[23],
#             },
#         "Business Wealth":{
#             "Business Wealth S.E": listD10[24],
#         }
#         },
#     "0-20": {
#         "Equities": {
#           '^GSPC': listD2[0],
#           '^FTSE': listD2[1],
#           '^STOXX': listD2[2],
#           '^IETP': listD2[3],
#           'IWDA.L': listD2[4],
#               },
#         "Bonds Short": {
#             # 'IB01.L': listD2[5],
#             'SHY': listD2[5],
#             'IGLS.L': listD2[6],
#             'SYB3.SW': listD2[7],
#             'Ire Short': listD2[8],
#             'IAGG': listD2[9],
#               },
#         "Bonds Long": {
#             'IEF': listD2[10],
#             'IGLT.L': listD2[11],
#             'SYBB.DE': listD2[12],
#             'Ire Long': listD2[13],
#             'EUN3.DE': listD2[14],
#             },
#         "Property":{
#             'Land Overall': listD2[15],
#             'Land HMR': listD2[16],
#             'Land': listD2[17],
#             'Land Other': listD2[18],
#             'Land UK': listD2[19],
#         },
#         "Deposits":{
#             'Overnight_Ire': listD2[20],
#             'ReedemableAtNotice': listD2[21],
#             'Agreed Maturity < 2': listD2[22],
#             'Agreed Maturity > 2': listD2[23],
#         },
#         "Business Wealth":{
#             "Business Wealth S.E": listD2[24],
#         }
#         },
#     "40-59": {
#         "Equities": {
#           '^GSPC': listD6[0],
#           '^FTSE': listD6[1],
#           '^STOXX': listD6[2],
#           '^IETP': listD6[3],
#           'IWDA.L': listD6[4],
#               },
#         "Bonds Short": {
#             # 'IB01.L': listD6[5],
#             'SHY': listD6[5],
#             'IGLS.L': listD6[6],
#             'SYB3.SW': listD6[7],
#             'Ire Short': listD6[8],
#             'IAGG': listD6[9],
#               },
#         "Bonds Long": {
#             'IEF': listD6[10],
#             'IGLT.L': listD6[11],
#             'SYBB.DE': listD6[12],
#             'Ire Long': listD6[13],
#             'EUN3.DE': listD6[14],
#             },
#         "Property":{
#             'Land Overall': listD6[15],
#             'Land HMR': listD6[16],
#             'Land': listD6[17],
#             'Land Other': listD6[18],
#             'Land UK': listD6[19],
#         },
#         "Deposits":{
#             'Overnight_Ire': listD6[20],
#             'ReedemableAtNotice': listD6[21],
#             'Agreed Maturity < 2': listD6[22],
#             'Agreed Maturity > 2': listD6[23],
#         },
#         "Business Wealth":{
#             "Business Wealth S.E": listD6[24],
#         }
#         }
#     # "Template": {
    #     "Equities": {
    #       '^GSPC':
    #       '^FTSE':
    #       '^STOXX':
    #       '^IETP':
    #       'IWDA.L':
    #           },
    #     "Bonds Short": {
    #         'IB01.L':
    #         'IGLS.L':
    #         'SYB3.SW':
    #         'Ire Short':
    #         'IAGG':
    #           },
    #     "Bonds Long": {
    #         'IEF':
    #         'IGLT.L':
    #         'SYBB.DE':
    #         'Ire Long':
    #         'EUN3.DE':
    #         },
    #     "Property":{
    #         'Overall Ire'
    #         'Overall UK'
    #     },
    #     "Deposits":{
    #         'Overnight Ire':
    #         'Overnight UK':
    #         'Agreed Maturity Ire':
    #         'Agreed Maturity UK':
    #     }
    #     }
    # }




def getCoeffs(assets, assetsCompleted, assetsYahoo, assetWeights, households, time, corrAbleClasses, returnsDict, inputParameters):


  daysPerYear = inputParameters["Overall"]["daysPerYear"]
  busEpsScalar = inputParameters["Busniess Equity"]["busEpsScalar"]
  alphaBus = inputParameters["Busniess Equity"]["alphaBusRaw"] / daysPerYear

  smallBlend = inputParameters["Busniess Equity"]["smallBlend"]
  largeBlend = inputParameters["Busniess Equity"]["largeBlend"]




  tickerToClass = {}
  for assetClass, tickers in assets.items():
    for ticker in tickers:
      tickerToClass[ticker] = assetClass






  # depositSeries = [2.63, 2.64, 2.60, 2.45, 2.28, 2.33, 2.26, 1.95, 1.97, 1.87, 1.88, 1.86, 1.93]
  depositSeries = [0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.14, 0.14, 0.13]
  depositSeries.reverse()
  if debug == True:
    print(depositSeries)
  list(depositSeries)
  depositRate = np.nanmean(depositSeries) / 100 / 252


  returnsDict = {}
  for assetClass in assets:
      returnsDict[assetClass] = {}
      for household in assetWeights:
        returnsDict[assetClass][household] = {}






  # for assetClass in assets:
  #   if assetClass not in returnsDict:
  #     returnsDict[assetClass] = {}
  #     returnsDict[assetClass] = addHouseholdsEmptyDict(returnsDict[assetClass])




  params_dict = {}
  if debug2 == True:
    for assetClass in assets:
        print(f"Asset Class is: {assetClass}")
        for asset in assets[assetClass]:
          print(f"Asset is {asset}, assetClass {assetClass}")
  coeffsDict = {}
  for assetClass in assets:
    if debug2 == True:
      print(f"AssetClass is {assetClass}")
    if assetClass not in coeffsDict:
      coeffsDict[assetClass] = {}
    for ticker in assets[assetClass]:
      if debug2 == True:
        print(f"Ticker is {ticker}")
      if ticker not in coeffsDict[assetClass]:
        coeffsDict[assetClass][ticker] = {}




  def getMu(ticker, coeffsDict):
      # muHist = np.nanmean(yf.download(ticker, start=start, end=end)['Close'].pct_change().dropna()) #for assetClass in assets for ticker_symbol in assets[assetClass]])
      for subheading, items in assets.items():
        if ticker in items:
          assetClass = subheading
          print(f"In getMu, asset is {ticker} and assetClass = {assetClass}")
      mu = coeffsDict[assetClass][ticker]['mu']
      # assetClass = tickerToClass[ticker]


      # muHist = coeffsDict[assetClass][ticker]['mu']
      # if debug == True:
      #   print("hist", muHist)
      # longRunPremium = 0.006
      # if ticker == 'Deposit':
      #   longRunPremium = 0.00001
      # # if ticker in assets["Equities"]:
      # #   longRunPremium = 0.009
      # # assert not isinstance(x, dict), "Tried to add a dict instead of numeric data"
      # muHistAnnual = (1 + muHist)**252 - 1
      # shrinkage = 0.25 # 0 is all historical, 1 is all long run
      # muShrunkAnnual = shrinkage * longRunPremium + (1 - shrinkage) * muHistAnnual
      # if debug == True:
      #   print("muShrunkAnnual", muShrunkAnnual)
      # mu = (1 + muShrunkAnnual)**(1/252) - 1
      # if ticker in assets["Equities"]:
      #   mu += 0.0001
      # if debug == True:
      #   print("mu in getMu is", mu)
      # if debug3 == True:
      #   print("mu in getMu is", mu)
      return mu

  uncorrZ = np.random.normal(0, 1, size=(len(assetsCompleted), (len(time))))






    # ___________________Data collection_________________________________


  def depositCleaning(data):
    annualRet = data / 100
    dailyRetSimple = annualRet / 12
    # dailyRetSimple is already a simple daily return, no need for log
    # dailyRetSeries = np.repeat(dailyRetSimple, (len(time)-2+len(dailyRetSimple))/len(dailyRetSimple))
    # dailyRetSeries = dailyRetSeries[:len(time)-2]
    # if debug4 == True:
      # print(f"Deposit daily ret = {dailyRetSimple}, and series len is {len(dailyRetSeries)}")
    return(dailyRetSimple)
  start = dt.datetime(2000, 1, 1)
  end = dt.datetime(2025, 1, 1)
  
  monthLength = 30
  for assetClass in assets:
    for ticker in assets[assetClass]:
      returns2 = None
      if assetClass in assetsYahoo:
        if ticker in assetsYahoo[assetClass]:  # Checking if asset is yahooable
          data = yf.download(ticker, start=start - dt.timedelta(days=1), end=end, progress=False) #getting data plus the day before the actual start date, for the first price
          # Calculated as simple returns
          if data.empty:
             raise RuntimeError(
              f"Data was empty for {ticker}, {assetClass} in getCoeffs"
             )
          if useLogs:
             returns = np.log(data['Close'].squeeze() / data['Close'].squeeze().shift(1)).dropna()
          else:
             returns = data['Close'].squeeze().pct_change().dropna()
          firstP = data['Close'].iloc[0]
          secondP = data['Close'].iloc[1] # Changed to get actual second price for starting the loop


          data = yf.download(ticker, start=start, end=end, progress=False) #getting data
          # Calculated as simple returns

          if useLogs:
             returns = np.log(data['Close'].squeeze() / data['Close'].squeeze().shift(1)).dropna()
          else:
             returns = data['Close'].squeeze().pct_change().dropna()
          if debugBus == True:
            print(f"proper, working {ticker} returns.shape {returns.shape}  mean {np.nanmean(returns)} returns[:50] {returns[:50]}")


          # print("raw mean", np.nanmean(returns))
          # print(" mean", np.nanmean(returns)/100)
          data = yf.download(ticker, start=start, end=end, progress=False)
          if debug == True:
            print("Woooooo over here **************************************************************************************", ticker, len(data))
        else:
          print(f"Skipping asset {ticker} because not Yahooable")
          continue
        # non Yahoo data collection hereeeeee +===============================================+ NON YAHOOOOOOOOO +=DA=DAHDOIASHDOI'ASNHDOASNBFASF
      elif assetClass == 'Business Wealth':
            if ticker == 'Business Wealth S.E':
              largeCapData = yf.download('^125904-USD-STRD', start=start, end=end, progress=False)
              smallCapData = yf.download('IEUS', start=start, end=end, progress=False)
              
              if debugBus == True:
                print(f"WOOOO BEFORE CHANGING ===================== largeCap.shape {largeCap.shape} mean {np.nanmean(largeCap)} type {type(largeCap)} largeCap[:50] {largeCap[:50]}")
              # if useLogs:
              #     smallCap = np.log(smallCapData['Close'].squeeze() / smallCapData['Close'].squeeze().shift(1)).dropna().squeeze()
              #     largeCap = np.log(largeCapData['Close'].squeeze() / largeCapData['Close'].squeeze().shift(1)).dropna().squeeze()
                  
              # else:
              smallCap = smallCapData['Close'].squeeze().pct_change().dropna().squeeze()
              largeCap = largeCapData['Close'].squeeze().pct_change().dropna().squeeze()
              largeCap, smallCap = largeCap.align(smallCap, join='inner')
              if debugBus == True:
                print(f"len(largeCap) {len(largeCap)}")
              smallCap = smallCap[:len(largeCap)]
              
            #  returns = np.log(data['Close'].squeeze() / data['Close'].squeeze().shift(1)).dropna()
            #   else:
                
           
              if debugBus == True:
                print(f"largeCap.shape {largeCap.shape} mean {np.nanmean(largeCap)} type {type(largeCap)} largeCap[:50] {largeCap[:50]}")
                print(f"smallCap.shape {smallCap.shape} mean {np.nanmean(smallCap)} smallCap[:50] {smallCap[:50]}")
              firstPLarge = float(largeCapData['Close'].squeeze().iloc[0])
              secondPLarge = float(largeCapData['Close'].squeeze().iloc[1])
              firstPsmall = float(smallCapData['Close'].squeeze().iloc[0])
              secondPsmall = float(smallCapData['Close'].squeeze().iloc[1])

              returns_simple = (largeCap * largeBlend + smallCap * smallBlend)
              # firstP = firstPLarge * largeBlend + firstPsmall * smallBlend
              # secondP = secondPLarge * largeBlend + secondPsmall * smallBlend

              if useLogs:
                returns = np.log1p(returns_simple)
              else:
                returns = returns_simple
              
              firstP = 100
              secondP = 100 * (1.0 + returns_simple)
                
              # am = arch_model(returns * 100, mean='Constant', vol='Garch', p=1, q=1, dist='gaussian')
              # resGARCH = am.fit(disp='off', show_warning=False, options={"maxiter": 150})

              if debugBus == True:
                print(f"returns.shape {returns.shape} type {type(returns)} mean {np.nanmean(returns)} returns[:50] {returns[:50]}")


      elif assetClass in assetsCompleted and assetClass != 'Business Wealth':
        if ticker in assetsCompleted[assetClass]:
          if assetClass == 'Property':
            runPropertyGarch = True
            if ticker == 'Land HMR':
              # Calculated as simple returns
              # returns2 = (dataHMR / dataHMR.shift(1) - 1)
              debugNew2 = True
              if useLogs:
                 returns2 = np.log(dataHMR / dataHMR.shift(1)).dropna()
              else:
                 returns2 = dataHMR.pct_change().dropna()
              histRetMonthly = returns2
              mu_monthly = np.nanmean(returns2)
              sigma_monthly = np.nanstd(returns2) # Array std dev
              coeffsDict[assetClass][ticker] = {
                 "mu_daily": mu_monthly / 21.0,
                 "sigma_daily": sigma_monthly / np.sqrt(21.0),
                 "histRetMonthly": returns2,
                 "firstP": 100.0
              }
              if debug12 == True:
                print(f"returns mean {np.nanmean(returns2)}")
              if debug8 == True or debugVolatility2:
                print(f"Returns 2 is {returns2}")
              # firstP and secondP are just placeholders, actual price series not used for GARCH directly
              if debugNew2:
                histRetAlmost = returns2 / monthLength
                print(f"Land HMR histRetAlmost mean: {np.nanmean(histRetAlmost):.6f}")

                histRet = np.repeat(histRetAlmost.values, monthLength)
                print(f"Land HMR histRet mean: {np.nanmean(histRet):.6f}")
                print(f"Land HMR histRet length: {len(histRet)}")
              firstP = 100.0
              secondP = 100.0
            elif ticker == 'Land Other':
              # Calculated as simple returns
              # returns2 = (dataLand / dataLand.shift(1) - 1)
              returns2 = dataLand.pct_change().dropna()
              returns2 = np.log1p(returns2)
              histRetMonthly = returns2
              mu_monthly = np.nanmean(returns2)
              sigma_monthly = np.nanstd(returns2)
              coeffsDict[assetClass][ticker] = {
                 "mu_daily": mu_monthly / 21,
                 "sigma_daily": sigma_monthly / np.sqrt(21.0), # BM scale to daily
                 "histRetMonthly": returns2,
                 "firstP": 100

              }
              
           
              if debug8 == True or debugVolatility2:
                print(f"Returns 2 for {ticker} is {returns2}")
              # firstP and secondP are just placeholders, actual price series not used for GARCH directly
              firstP = 100.0
              secondP = 100.0
            continue
          elif assetClass == 'Deposits':
            if ticker == 'Overnight_Ire':
              returns2 = depositCleaning(dataOvernight)
              returns2 = np.log1p(returns2)
              coeffsDict[assetClass][ticker]['histRetMonthly'] = returns2
              histRetMonthly = returns2
              mu_monthly = np.nanmean(returns2)
              sigma_monthly = np.nanstd(returns2)
              coeffsDict[assetClass][ticker] = {
                 "mu_daily": mu_monthly / 21,
                 "sigma_daily": sigma_monthly / np.sqrt(21.0), # BM scale to daily
                 "histRetMonthly": returns2,
                 "firstP": 100

              }
            elif ticker == 'ReedemableAtNotice':
              returns2 = depositCleaning(dataReedemable)
              returns2 = np.log1p(returns2)
              histRetMonthly = returns2
              mu_monthly = np.nanmean(returns2)
              sigma_monthly = np.nanstd(returns2)
              coeffsDict[assetClass][ticker] = {
                 "mu_daily": mu_monthly / 21,
                 "sigma_daily": sigma_monthly / np.sqrt(21.0), # BM scale to daily
                 "histRetMonthly": returns2,
                 "firstP": 100

              }
            elif ticker == 'Agreed Maturity < 2':
              returns2 = depositCleaning(dataAgreedShort)
              returns2 = np.log1p(returns2)
              histRetMonthly = returns2
              mu_monthly = np.nanmean(returns2)
              sigma_monthly = np.nanstd(returns2)
              coeffsDict[assetClass][ticker] = {
                 "mu_daily": mu_monthly / 21,
                 "sigma_daily": sigma_monthly / np.sqrt(21.0), # BM scale to daily
                 "histRetMonthly": returns2,
                 "firstP": 100

              }
            elif ticker == 'Agreed Maturity > 2':
              returns2 = depositCleaning(dataAgreedLong)
              returns2 = np.log1p(returns2)
              histRetMonthly = returns2
              mu_monthly = np.nanmean(returns2)
              sigma_monthly = np.nanstd(returns2)
              coeffsDict[assetClass][ticker] = {
                 "mu_daily": mu_monthly / 21,
                 "sigma_daily": sigma_monthly / np.sqrt(21.0), # BM scale to daily
                 "histRetMonthly": returns2,
                 "firstP": 100

              }
            continue
          # if returns2 is not None:
          #   # coeffsDict[assetClass][ticker] = returns2
          #   returns2 = np.log1p(returns2)
          #   histRetMonthly = returns2
            
          #   mu_monthly = np.nanmean(returns2)
          #   sigma_monthly = np.nanstd(mu_monthly)
          #   coeffsDict[assetClass][ticker] = {
          #       "mu_daily": mu_monthly / 21,
          #       "sigma_daily": sigma_monthly / np.sqrt(21.0), # BM scale to daily
          #       "histRetMonthly": returns2,
          #       "firstP": 100

          #   }
          # returns2 = np.log1p(returns2)
          histRetMonthly = returns2
          if debugVolatility3:
            print(f"{ticker} {assetClass}: {histRetMonthly}")


  # Self Employeed Bus wealth = SMEA.L (large), start=2009; iShares MSCI Europe Small-Cap ETF (IEUS) (small), start=2008






      #_______ Running / defining GARCH for Non Yahoo, Monthly _____________________________-r
      #-----------------------------------------------------------------------------q
          if debug2 == True:
            print("In getting Coeefs (runnin Garch for non Yahoo), returns 2 is ", returns2)

          am = arch_model(returns2, mean='Constant', lags=0, vol='Garch', p=1, q=1, dist='gaussian', hold_back=None, rescale=None)
          resGARCH = am.fit(disp='off', show_warning=False, options={"maxiter": 150})
          params_dict[ticker] = resGARCH.params


          monthLength = 30
          adjustment = 0
          #extracting coefficents
          # mu from GARCH is mean of simple returns. Scaling for daily.
          mu = params_dict[ticker]['mu'] / monthLength
          # mu = getMu(ticker)
          assert not isinstance(mu, dict), "Tried to add a dict instead of numeric data"
          # mu = mu + np.random.normal(0, 0.00002)
          if debug == True:
            print('mu is', mu)
          omega = params_dict[ticker]['omega']
          alpha1 = params_dict[ticker]['alpha[1]']
          beta1 = params_dict[ticker]['beta[1]']
          fitSigma = resGARCH.conditional_volatility / np.sqrt(monthLength)
          if debug8 == True:
            print(f"initilisation of fitSigma for {ticker} mean {np.nanmean(fitSigma)}, first 20 {fitSigma[:20]}")
            print(f"Alpha1 {alpha1}, beta1 {beta1}, sum {alpha1 + beta1}, omega {omega}")


          #aggregating to len(time)


          sigmaDailySeries = np.repeat(fitSigma.values, monthLength)
          if len(sigmaDailySeries) < len(time):
            if debug4 == True:
              print(f"{ticker}, sigmaDailySeries: {sigmaDailySeries}")
            sigmaDailySeries = np.pad(sigmaDailySeries, (0, len(time) - adjustment - len(sigmaDailySeries)), mode='edge')
          # histRetAlmost is simple monthly return, scaled for daily.


          histRetAlmost = returns2 / monthLength


          if debug4 == True:
            print("Mu shape / type, ", type(mu), getattr(mu, 'shape', None))
          muDaily = np.full((len(time) - adjustment), mu)
          # sigmaDailySeries = sigmaDailySeries[:len(time)]
          histRet = np.repeat(histRetAlmost.values, monthLength)


          if len(histRet) < len(time):
            if debug4 == True:
              print(f"{ticker}, histRet {histRet}")
            if debug12 == True:
              print(f"histRet mean before padding {np.nanmean(histRet)}")
            histRet = np.pad(histRet, (0, len(time) - adjustment - len(histRet)), mode='edge')
          # print("WOOOOO, histRet is here: ", histRet)
          # histRet = returns2
          if debug2 == True:
            print(f"histRet Len {asset} {assetClass} = ", len(histRet))
            print(f"HistRet in non yahooable, {asset} {assetClass} is ", histRet)
          muHist = np.nanmean(histRetAlmost)
          # nonLogRet = returns2
          # sigma = np.nanstd(histRetAlmost) / np.sqrt(histRetAlmost)

          sigma = np.nanstd(histRetMonthly)
          if debug12 == True:
            print(f"returns 2 mean {ticker} {np.nanmean(returns2)}, histRetAlmost mean {np.nanmean(histRetAlmost)} histRet mean {np.nanmean(histRet)}")
          coeffsDict[assetClass][ticker] = {
              'omega': omega,
              'alpha1': alpha1,
              'beta1': beta1,
              'beta2': 0,
              'sigmaScalar': sigma,
              'fitSigma': sigmaDailySeries,
              'histRet': None,
              'muHist': muHist,
              'mu': muHist,
              'muDaily': muDaily,
              'firstP': firstP,
              'secondP': secondP,
              'histRetMonthly': histRetMonthly
              }
          if debug5 == True:
            print(f"saved coeffsDict for {ticker} in {assetClass}, GARCH for Non Yahoo")
            print("Type:", type(coeffsDict[assetClass][ticker]))
            print("Keys of coeffsDict[assetClass][ticker]", coeffsDict[assetClass][ticker].keys())
            print(f"Asset class: {assetClass}, ticker: {ticker}")
          # return(r, cumR, p, sigma, fitSigma, time, areDeposit)


        if assetClass == 'Deposits':
          
          continue
        elif assetClass == 'Business Wealth':
          donothing = 1


        else:
          if debug5 == True:
            print(f"Skipping asset {ticker} because not completed")
          continue
      else:
        if debug5 == True:
          print(f"Skipping asset class {assetClass} because not completed")
        continue


      # elif ticker == 'Ire Short':
      #   data = ('uh idk')
      # elif ticker == 'Ire Long':
      #   data = ('uh idk')
      # elif ticker == 'Overall Ire':
      #   data = ('uh idk')
      # elif ticker == 'Overall UK':
      #   data = ('uh idk')
      # elif ticker == 'Overnight Ire':
      #   data = ('uh idk')
      # elif ticker == 'Overnight UK':
      #   data = ('uh idk')
      # elif ticker == 'Agreed Maturity Ire':
      #   data = ('uh idk')
      # elif ticker == 'Agreed Maturity UK':






      # __________________Defining Model____________________________________
      if debug2 == True:
        print("In getting Coeefs (runnin Garch for Yahoo), returns is ", returns)
      am = arch_model(returns, mean='Constant', lags=0, vol='Garch', p=1, q=2, dist='gaussian', hold_back=None, rescale=None)
      resGARCH = am.fit(disp='off', show_warning=False, options={"maxiter": 150})
      params_dict[ticker] = resGARCH.params


    # ____________________extracting coefficents____________________________


      # mu from GARCH is mean of simple returns
      mu = params_dict[ticker]['mu']
      assert not isinstance(mu, dict), "Tried to add a dict instead of numeric data"
      # mu = mu + np.random.normal(0, 0.00002)
      if debug == True:
        print('mu is', mu)
        print("Now extracting coefficents")
      omega = params_dict[ticker]['omega']
      alpha1 = params_dict[ticker]['alpha[1]']
      beta1 = params_dict[ticker]['beta[1]']
      beta2 = params_dict[ticker]['beta[2]']
      fitSigma = resGARCH.conditional_volatility
      histRet = returns
      if debug2 == True:
        print("Length of HistRet in yahooable is ", len(histRet))
        print("HistRet in yahooable is ", histRet)
      # print("WOOOOO, histRet is here: ", histRet)
      muHist = np.nanmean(returns)
      mu = muHist
      coeffsDict[assetClass][ticker] = {
          'omega': omega,
          'alpha1': alpha1,
          'beta1': beta1,
          'beta2': beta2,
          'fitSigma': fitSigma,
          'histRet': histRet,
          'muHist': muHist,
          'firstP': firstP,
          'secondP': secondP,
          'mu': mu
      }
      if debug4 == True:
        print("This is the Yahooable one")
        print("Type:", type(coeffsDict[assetClass][ticker]))
        print("Keys of coeffsDict[assetClass][ticker]", coeffsDict[assetClass][ticker].keys())
        print(f"Asset class: {assetClass}, ticker: {ticker}")
      # print(coeffsDict)
  
  
  #================================================
  # Correlation matrix + tickers ordered generation
  #================================================
  closeDict = {}
  for assetClass in assets:
      for ticker in assets[assetClass]:
          if assetClass in assetsCompleted and ticker in assetsCompleted[assetClass] and assetClass in corrAbleClasses:
              raw = coeffsDict[assetClass][ticker].get('histRet', None)
              if raw is None:
                continue
              closeDict[ticker] = np.asarray(raw).ravel()
  # timeDT = pd.to_datetime(time)
  timeDT = pd.DatetimeIndex(pd.to_datetime(time))



  # minLen = min(len(v) for v in closeDict.values())
  print(f"[DEBUG] closeDict keys ({len(closeDict)}): {sorted(closeDict.keys())}")
  all_daily_candidates = []
  for assetClass in assets:
      for ticker in assets[assetClass]:
          if assetClass in assetsCompleted and ticker in assetsCompleted[assetClass] and assetClass in corrAbleClasses:
              all_daily_candidates.append((assetClass, ticker))
  print(f"[DEBUG] eligible (assetClass,ticker) pairs ({len(all_daily_candidates)}): {all_daily_candidates}")
  missing = [(ac, t) for ac, t in all_daily_candidates if t not in closeDict]
  print(f"[DEBUG] eligible but missing from closeDict: {missing}")
  for ac, t in missing:
    has_key = 'histRet' in coeffsDict.get(ac, {}).get(t, {})
    val = coeffsDict.get(ac, {}).get(t, {}).get('histRet', '<no key>')
    print(f"[DEBUG]   {ac}/{t}: has histRet key={has_key}, value type={type(val)}")
  minLen = min(len(v) for v in closeDict.values()) if closeDict else 0
  # useIndependentNoise = (minLen < 2) or (len(closeDict) < 2)
  useIndependentNoise = (minLen < 100) or (len(closeDict) < 2)
  if useIndependentNoise:
        print(f"WARNING: Using independent noise (minLen={minLen}, n_assets={len(closeDict)})")

  if closeDict:
    # Fensure alignment
    minLen = min(len(v) for v in closeDict.values())

    
    for ticker in closeDict:
        closeDict[ticker] = closeDict[ticker][-minLen:]

    # Create time index matching the trimmed data length
    timeDT = pd.DatetimeIndex(pd.to_datetime(time[-minLen:]))

    # Build DataFrame with explicit index matching data length
    allClosePrices = pd.DataFrame(closeDict)
    allClosePrices.index = timeDT
    allReturns = allClosePrices.dropna()

    # Check if have enough rows for correlation
    if len(allReturns) < 2:
        dailyTickers = []
        corrDaily = np.array([[1.0]])
        allReturns = pd.DataFrame()
    else:
        dailyTickers = list(allReturns.columns)
        corrDaily = np.corrcoef(allReturns.values.T)
  else:
      dailyTickers = []
      corrDaily = np.array([[1.0]])
      allReturns = pd.DataFrame()
  print(f"[DEBUG] dailyTickers={len(dailyTickers)}, allReturns.empty={allReturns.empty if 'allReturns' in dir() else 'undefined'}")
  monthlyData = {}
  for assetClass in ['Property', 'Deposits']:
      if assetClass in coeffsDict:
          for ticker in coeffsDict[assetClass]:
              raw = coeffsDict[assetClass][ticker].get('histRetMonthly',
                    coeffsDict[assetClass][ticker].get('histRet', None))
              if raw is None:
                  continue

              # Convert to Series
              if isinstance(raw, pd.Series):
                  s = raw.copy()
              else:
                  s = pd.Series(np.asarray(raw).ravel())

              # Only assign index if it doesn't have one or has wrong length
              if not isinstance(s.index, pd.DatetimeIndex) or len(s.index) != len(s):
                  s.index = pd.date_range(
                      start=pd.Timestamp('2010-01-01'),
                      periods=len(s),
                      freq='MS'
                  )

              monthlyData[ticker] = s

  #  Only create DataFrame if have data
  if monthlyData:
      dfMonthly = pd.DataFrame(monthlyData).dropna()
      print(f"[DEBUG] dfMonthly.shape={dfMonthly.shape}, len(dfMonthly)={len(dfMonthly)}")
      if len(dfMonthly) < 2:
          monthlyTickers = []
          corrMonthly = np.array([[1.0]])
      else:
          monthlyTickers = list(monthlyData.keys())
          corrMonthly = np.corrcoef(dfMonthly.values.T)
  else:
      monthlyTickers = []
      corrMonthly = np.array([[1.0]])
  if not allReturns.empty and not dfMonthly.empty:
    # Resample daily returns to monthly
    allReturns_dt = allReturns.copy()
    allReturns_dt.index = pd.to_datetime(allReturns_dt.index).normalize()

    monthly_cols = {}
    for col in allReturns_dt.columns:
        resampled = (1 + allReturns_dt[col]).resample('MS').prod() - 1
        monthly_cols[col] = resampled

    dfDailyMonthly = pd.DataFrame(monthly_cols)

    # define commonIDX
    commonIDX = dfDailyMonthly.index.intersection(dfMonthly.index)

    # run the cross-correlation block
    if len(commonIDX) >= 2:
        crossDataDaily = dfDailyMonthly.loc[commonIDX].values
        crossDataMonthly = dfMonthly.loc[commonIDX].values


        n_d = len(dailyTickers)
        n_m = len(monthlyTickers)
        corrCross = np.zeros((n_d, n_m))

        for i in range(n_d):
            for j in range(n_m):
                if crossDataDaily.shape[1] > i and crossDataMonthly.shape[1] > j:
                    c = np.corrcoef(crossDataDaily[:, i], crossDataMonthly[:, j])[0, 1]
                    corrCross[i, j] = c if np.isfinite(c) else 0.0
    else:
        # Fallback: zero correlations
        n_d = len(dailyTickers)
        n_m = len(monthlyTickers)
        corrCross = np.zeros((n_d, n_m))
  #  SAFE DEFAULT for empty case
  nTotal = n_d + n_m
  if nTotal == 0:
      nTotal = 1
      fullCorr = np.array([[1.0]])
      L = np.array([[1.0]])
      allTickersOrdered = []
  else:
      fullCorr = np.eye(nTotal)  # Start with identity

      if n_d > 0:
          if len(dailyTickers) > 1:
              fullCorr[:n_d, :n_d] = corrDaily
          else:
              fullCorr[:n_d, :n_d] = np.array([[1.0]])

      if n_m > 0:
          if len(monthlyTickers) > 1:
              fullCorr[n_d:, n_d:] = corrMonthly
          else:
              fullCorr[n_d:, n_d:] = np.eye(n_m)

      if n_d > 0 and n_m > 0:
          fullCorr[:n_d, n_d:] = corrCross
          fullCorr[n_d:, :n_d] = corrCross.T

  allTickersOrdered = dailyTickers + monthlyTickers
  # apply any modifers for testing
  fullCorr = applyCorrelationModifer(fullCorr, allTickersOrdered, assets, inputParameters)
  # Regularize and compute Cholesky
  fullCorr = fullCorr + 1e-6 * np.eye(nTotal)

  eigvals = np.linalg.eigvals(fullCorr)
  if np.min(eigvals.real) < 0:
      # fullCorr += (-np.min(eigvals.real) + 1e-6) * np.eye(nTotal)
      # 1. Shift to make positive definite
      shift = -np.min(eigvals.real) + 1e-6
      fullCorr += shift * np.eye(nTotal)
      
      # 2. Scale back to a true correlation matrix (diagonals = 1.0)
      
      d = 1.0 / np.sqrt(np.diag(fullCorr))
      fullCorr = fullCorr * np.outer(d, d)
  if debugCorrelation:
      print("\nFINAL CORR MATRIX")
      print(
          "Mean corr:",
          np.mean(fullCorr[np.triu_indices_from(fullCorr, k=1)])
      )
      print(
          "Min eig:",
          np.linalg.eigvalsh(fullCorr).min()
      )
  return coeffsDict, returnsDict, fullCorr, allTickersOrdered


def runAssetSimul(ticker, z, coeffsDict, assetWeights, assetsCompleted, time, rng=None, busEpsScalar=1.1, alphaBus=None):
  assets = assetsCompleted
  def _makeSmall(series, name):
      limit = 300
      # Convert single-column DataFrame to Series for consistent integer-based indexing
      # if isinstance(series, pd.DataFrame) and series.shape[1] == 1:
      #     series = series.iloc[:, 0]
      print(f"Mean {name}: {np.nanmean(series)}, std {np.nanstd(series)}")
      D1 = series[:int(len(series) / 10)]
      D10 = series[int((len(series) / 10) * 9):]
      # D1 = series[(len(series) - 10]
      print(f"First 10 items in {name}: {series[:10]}")
      print(f"Mean of first 10% of {name}: {np.nanmean(D1)}, std {np.nanstd(D1)}")
      print(f"Mean of last 10% of {name}: {np.nanmean(D10)}, std {np.nanstd(D10)}")
      newSeries = [] # Initialize newSeries outside the if block
      if len(series) > limit:
        for i in range(len(series)):
          if debug6 == True:
            if i % 100 == 0:
              print(f"i is {i}, series{i} is {series[i]} ")
              print(f"(len(series) / limit) {(len(series) / limit)}")
          if i % int(len(series) / limit) == 0:
            newSeries.append(series[i])
            if debug6 == True:
              print(f"series being appended, len is {len(newSeries)}")
      print(f"len of new {name} {len(newSeries)}") 
      return newSeries
  if rng == None:
     rng = np.random.default_rng()
     print(f"NO RNG FOR {ticker}!! notice_me!!!!")
  
  
  if debugVolatility2:
    print("RUN ASSET SIMUL START", ticker)
    # print("PROPERTY BRANCH", ticker)
    for name, value in {
      # "histRetMonthly": histRetMonthly,
      # "histRet": histRet,
      "z": z,
      "time": time, }.items():
      try:
          print(name, np.shape(value))
      except:
          pass
  targetLen = len(time) #- 2
  # z = z[:targetLen]
  z = np.asarray(z[:targetLen], dtype=np.float64)

  for subheading, items in assets.items():
    if ticker in items:
      assetClass = subheading
  if debug3 == True:
    print(f"Ticker = {ticker}, AssetClass = {assetClass}")
  if assetClass == 'Deposits' and False:
    muMonthly = coeffsDict[assetClass][ticker]['mu'] # Base (simple) hist returns
    if isinstance(muMonthly, pd.Series):
            muMonthly = muMonthly.values

    monthsNeeded = int(np.ceil(targetLen / 30)) + 1
    sampledMonthly = np.random.choice(muMonthly, size=monthsNeeded, replace=True)

    muVol = np.nanstd(muMonthly) / np.sqrt(30)
    if muVol <= 0.00002: # fallback if tiny mu volatility
      muVol = 0.00002
    z = z[:targetLen]
    if len(muMonthly) < targetLen:
        mu_daily = np.repeat(muMonthly, int(np.ceil(targetLen / len(muMonthly))))[:targetLen]
    else:
        mu_daily = mu[:targetLen]
    # if isinstance(mu_daily, (np.ndarray, pd.Series)):
    #     # Create daily index
    #     daily_dates = np.arange(targetLen)
    #     # Monthly indices (spread evenly over the daily range)
    #     monthly_indices = np.linspace(0, targetLen-1, len(muMonthly))
    #     # Interpolate
    #     from scipy import interpolate
    #     f = interpolate.interp1d(monthly_indices, mu_daily, kind='linear', fill_value='extrapolate')
    #     mu_daily = f(daily_dates)

    # else:
        # mu_daily = float(mu_daily)
    mu_daily = mu_daily / 30
    r = mu_daily + muVol * z
    if isinstance(r, pd.Series):
            r = r.values
    firstP = coeffsDict[assetClass][ticker]['firstP']
    if isinstance(firstP, (pd.Series, pd.DataFrame)):
        firstP = float(firstP.iloc[0] if hasattr(firstP, 'iloc') else firstP)
    # For simple returns, cumulative product of (1 + r) is used for price
    cumR = np.cumprod(1 + r) - 1 # Cumulative simple return
    explode_test(1000000, cumR, "Deposits in runassetSimul")
    if isinstance(firstP, pd.Series):
      firstP = float(firstP.iloc[0])



    if isinstance(firstP, pd.DataFrame):
      firstP = float(firstP.iloc[0, 0])

    p = firstP * np.cumprod(1 + r)
    # sigma = np.zeros_like(r)
    sigma = np.full_like(r, muVol)
    areDeposit = False
    assert len(r) == targetLen, f"Length mismatch for {ticker}: expected {targetLen}, got {len(r)}"
    return (r, cumR, p, sigma, sigma, time, areDeposit)
# _________Getting White Noise (z)_____________________
  # Initialize z once for the simulation path
  # print(f"z in {ticker} len {len(z)}")
  zMean = np.nanmean(z)


  zStd = np.nanstd(z)


  zVariance = np.var(z)




  if debug4 == True:
    print("Simulation is now runAssetSimul")
    print('Mean is ', zMean)
    print('Std is ', zStd)
    print('Variance is ', zVariance)
    print('len(time) is ', len(time))
  # print('len(number) is ', len(z))

  




  #__________________________day 1______________________
  #t-1 for the first day would be an error as there is prior value. So, I'm getting the values from the last historic day


  #getting the fitted (based on actual historic data) versions of simga and epsilon






  # if assetClass in assetsCompleted and assetClass not in assetsYahoo:
  if assetClass == 'Property' or assetClass == 'Deposits':

    if ticker in assetsCompleted[assetClass]:
      # if assetClass in ['Property', 'Deposits']:
      mu_d = coeffsDict[assetClass][ticker]['mu_daily']
      sig_d = coeffsDict[assetClass][ticker]['sigma_daily']
      firstP = coeffsDict[assetClass][ticker]['firstP']
      
      # Simulate daily log returns using scaled monthly moments
      r = mu_d + sig_d * z[:targetLen]
      
      # Convert log returns to cumulative simple returns
      cumR = np.exp(np.cumsum(r)) - 1
      p = firstP * np.exp(np.cumsum(r))
      
      sigma = np.full_like(r, sig_d)
      areDeposit = (assetClass == 'Deposits')
      explode_test(1000000, cumR, "Property in runassetSimul")
      r_simple = np.exp(r) - 1.0
      if debugVolatility2:
        print("PROPERTY DEBUG")
        print("ticker", ticker)
        print("mu shape", np.shape(mu))
        # print("sigmaScalar shape", np.shape(sigmaScalar))
        print("z shape", np.shape(z))
      return r_simple, cumR, p, sigma, sigma, time, areDeposit # sigma 2 = fitSigma
      #--------------
      # GARCH running
      #--------------
      # fitSigma = coeffsDict[assetClass][ticker]['fitSigma']
      # sigmaScalar = coeffsDict[assetClass][ticker]['sigmaScalar']
      # if debug8 == True:
      #   print(f"fit Sigma mean {np.nanmean(fitSigma)}, first 20 items {fitSigma[:20]}")


      #   plt.plot(time[:len(fitSigma)], fitSigma)
      #   plt.title(f"Fit Sigma for {ticker}")
      #   plt.xlabel("Date")
      #   plt.ylabel("Sigma")
      #   plt.show()
      #   _makeSmall(fitSigma, {ticker})
      # omega = coeffsDict[assetClass][ticker]['omega']
      # alpha1 = coeffsDict[assetClass][ticker]['alpha1']
      # beta1 = coeffsDict[assetClass][ticker]['beta1']
      # mu = coeffsDict[assetClass][ticker]['mu']


      # firstP = coeffsDict[assetClass][ticker]['firstP']
      # secondP = coeffsDict[assetClass][ticker]['secondP']
      # if debug14 == True:
      #   print("Type:", type(coeffsDict[assetClass][ticker]))
      #   print("Keys (day 1 runAssetSimul) of coeffsDict[assetClass][ticker]", coeffsDict[assetClass][ticker].keys())
      #   print(f"Asset class: {assetClass}, ticker: {ticker}")
      # # print("Type of obj ", type(obj))
      # # print("Keys of obj ", obj.keys())
      # # mu = coeffsDict[assetClass][ticker]['mu']
      # # mu = getMu(ticker)
      # # mu = coeffsDict[assetClass][ticker]['mu']
      # if debug4 == True:
      #   print(f"In runAssetSimul, mu = {coeffsDict[assetClass][ticker]['mu']}")
      # # print(f"shape of fitSigma: {fitSigma}, shape of z[2:len(time)] = {z[2:len(time)]}")
      #   print("Time is ==== ", time)


      #   print(f"{ticker} In runAssetSimul, len of z[2:len(time)] = {len(z[2:len(time)])}")
      #   print(f"{ticker} In runAssetSimul, len(time) = {len(time)}")
      #   print(f"{ticker} In runAssetSimul, fitSigma = {fitSigma}")
      #   print(f"{ticker} In runAssetSimul, len fitSigma = {len(fitSigma)}")
      #   print(f"{ticker} In runAssetSimul, z = {z}")
      #   print(f"{ticker} In runAssetSimul, len(z) = {len(z)}")
      # # fitSigma2d = fitSigma[np.newaxis, :]#ensuring proper alignment this is where it is a series
      # # r = mu + fitSigma2d * z[2:len(time)]

      # if debugVolatility2:
      #   print("PROPERTY DEBUG")
      #   print("ticker", ticker)
      #   print("mu shape", np.shape(mu))
      #   print("sigmaScalar shape", np.shape(sigmaScalar))
      #   print("z shape", np.shape(z))

      # def align_for_sim(mu, sigma, z):

      #   z = np.asarray(z)

      #   arrays = []

      #   if not np.isscalar(mu):
      #       mu = np.asarray(mu)
      #       arrays.append(mu)

      #   if not np.isscalar(sigma):
      #       sigma = np.asarray(sigma)
      #       arrays.append(sigma)

      #   arrays.append(z)

      #   n = min(len(x) for x in arrays)

      #   if not np.isscalar(mu):
      #       mu = mu[:n]

      #   if not np.isscalar(sigma):
      #       sigma = sigma[:n]

      #   z = z[:n]

      #   return mu, sigma, z

      # firstSigma = fitSigma.iloc[-1] / np.sqrt(30) if hasattr(fitSigma, 'iloc') else fitSigma[-1] / np.sqrt(30)
      # firstEps = firstSigma * rng.normal()

      # mu, sigmaScalar, z = align_for_sim(mu, sigmaScalar, z)
      # targetLen = len(time) - 2
      # z = z[:targetLen+2]
      # # r = mu + sigmaScalar * z # still simple returns
      # # sigma = sigmaScalar * z

      # # runnning GARCH
      # r, sigma, eps = _garch_loop(
      #   z.astype(np.float64),
      #   float(mu / 30),
      #   float(omega / 30),
      #   float(alpha1 / np.sqrt(30)), #approx
      #   float(beta1 / np.sqrt(30)),
      #   0.0, #no beta 2
      #   float(firstSigma),
      #   float(firstEps)
      # )
      # if debug12 == True:
      #   print(f"{ticker} HEYY IN RUNASSETSIMUL PROPERTY mean r {np.nanmean(r)}, mu {mu}, sigmaScalar {sigmaScalar}, sigma mean {np.nanmean(sigma)}, sigma std {np.nanstd(sigma)}, z mean {np.nanmean(z)}, z std {np.nanstd(z)}")
      # # r = mu + fitSigma2d * z # r will be simple returns


      # cumR = np.cumprod(1 + r) - 1 # Cumulative simple return
      # explode_test(1000000, cumR, "Property in runassetSimul")

      # if isinstance(firstP, pd.Series):
      #   firstP = float(firstP.iloc[0])



      # if isinstance(firstP, pd.DataFrame):
      #   firstP = float(firstP.iloc[0, 0])


      # p = firstP * np.cumprod(1 + r)
      # if debug4 == True:
      #  print("fitSigma shape / type, ", type(fitSigma), getattr(fitSigma, 'shape', None))
      # # sigma = np.full(len(r), fitSigma)
      # # fitSigma = sigma
      # areDeposit = False
      # if debug2 == True:
      #   # print(f"In runAssetSimul,(non yahoo), r = {r}, cumR, p, sigma, fitSigma, time, areDeposit = ", cumR, p, sigma, fitSigma, time, areDeposit)


      #   print(f"In runAssetSimul, r mean = {np.nanmean(r)}, cumR, p, sigma, fitSigma, time, areDeposit = ")
      # # sigma = fitSigma
      # # sigma = sigmaScalar + np.random.normal(0, 0.0001, size=len(r))
      # if debugVolatility2:
      #   print(f"Ticker {ticker}")
      #   print("len(r)", len(r))
      #   print("len(z)", len(z))
      #   print("len(time)", len(time))
      #   # print("len(portRet)", len(portRet))
      #   # print("len(portSig/ma)", len(portSigma))
      # return(r, cumR, p, sigma, fitSigma, time, areDeposit)

  # if not property:
  omega = coeffsDict[assetClass][ticker]['omega']
  alpha1 = coeffsDict[assetClass][ticker]['alpha1']
  beta1 = coeffsDict[assetClass][ticker]['beta1']
  beta2 = coeffsDict[assetClass][ticker]['beta2']
  fitSigma = coeffsDict[assetClass][ticker]['fitSigma']
  if debug4 == True:
    print(f"FitSigma in day 1 grounding for {ticker} is ", fitSigma)
  firstP = coeffsDict[assetClass][ticker]['firstP']
  secondP = coeffsDict[assetClass][ticker]['secondP']
  fitEps = coeffsDict[assetClass][ticker]['histRet'] - coeffsDict[assetClass][ticker]['mu']
  longVar = omega / (1 - alpha1 - beta1 - beta2)
  if debug10== True:
    print(f"{ticker} longVar {longVar}")
    print(f"{ticker} sum of Alpha1 {alpha1} beta1 {beta1} and beta2 {beta2} {beta2 + alpha1 + beta1}")
  # unconditionalSigma = np.nanmean(fitSigma)
  # firstSigma = unconditionalSigma * (1 + np.random.normal(0, 0.1))
  # secondSigma = unconditionalSigma * (1 + np.random.normal(0, 0.1))


  # firstSigma = fitSigma.iloc[-2].item()
  # secondSigma = fitSigma.iloc[-1].item()
  # firstSigma = fitSigma.iloc[-2]
  # secondSigma = fitSigma.iloc[-1]
  firstSigma = np.sqrt(longVar)


  secondSigma = firstSigma
  firstEps = firstSigma * rng.normal()
  # firstEps = fitEps.iloc[-1]
  # firstEps = fitEps.iloc[-1].item()
  if debug == True:
    print('first sigma is', firstSigma, 'second sigma is ', secondSigma, 'firstEps is ', firstEps)
    print("Simulation is now day 1")
  if debug8 == True:
    print(f"first sigma is", firstSigma, 'second sigma is ', secondSigma, 'firstEps is ', firstEps)
    print(f"fitEps is {fitEps}, coeffsDict[assetClass][ticker][histRet] {coeffsDict[assetClass][ticker]['histRet']}, coeffsDict[assetClass][ticker][mu], {coeffsDict[assetClass][ticker]['mu']}")
    print("Simulation is now day 1")

  # defining return, sigma, epsilon and prices lists, as well as euluer

  r = []
  sigma = [firstSigma, secondSigma]
  eps = [firstEps, firstEps] # list lenghts must match
  if debug10== True and assetClass == 'Property':
    print(f"Eps for {ticker} starting 2 values {eps}")
  p = [firstP, secondP] #prices
  e = np.exp(1) #euler
  if debug == True:
    print("non deposit")







  # mu = (1 + muHist) ** 252 -1







  # mu = getMu(ticker) # + np.random.normal(0, 0.00005)

    # print("mean(fitSigma)", unconditionalSigma)


  mu = coeffsDict[assetClass][ticker]['mu']
  assert not isinstance(mu, dict), "Tried to add a dict instead of numeric data"
  if debug == True:
    print("mu daily is", mu)
  
  #   for t in range(2, len(time)):
  #     newSigma = (omega + alpha1 * eps[t-1]**2 + beta1 * sigma[t-1]**2 + beta2 * sigma[t-2]**2)**0.5
  #     sigma.append(newSigma)
  #     if debug9 == True and assetClass == 'Property':
  #       print(f"{ticker} len z {len(z)}, z {z}")
  #     newEps = newSigma * z[t]
  #     # negative = False
  #     # if newEps < 0:
  #     #   negative = True
  #     # newEps = min(int(np.abs(newEps)*100), int(100*0.05)) / 100
  #     # if negative == True:
  #     #   newEps = newEps * -1
  #     eps.append(newEps)
  #     newR = mu + newEps * busEpsScalar + alphaBus # newR represents a simple return




  #     r.append(newR)
  #     # The price update formula, assuming newR is a simple return
  #     newP = p[t-1] * (1 + newR)
  #     p.append(newP)
  #   if debug10== True or debug11 == True or debugBus == True:
  #     print(f"omega {omega}, alpha1 {alpha1}, beta1 {beta1}, beta2 {beta2}, eps[:50] {eps[:50]}, sigma[:50] {sigma[:50]}")
  #   if debugBus == True:
  #     print("Sigma mean: ", np.nanmean(sigma))
  #     print("New Sigma", newSigma)
  #     print("newEps", newEps)
  #     print("Eps mean", np.nanmean(eps))
  #     print("Simulation is now running for t")


  #   # Calculate cumulative simple returns after the loop
  #   cumR = np.cumprod(1 + np.array(r)) - 1
  z = np.asarray(z[:targetLen], dtype=np.float64)
  r, sigma, eps = _garch_loop(
    z.astype(np.float64),
    float(mu),
    float(omega),
    float(alpha1),
    float(beta1),
    float(beta2),
    float(firstSigma),
    float(firstEps)
)
  r_simple = np.exp(r) - 1.0 # Convert to simple returns for valid portfolio aggregation
  if ticker == 'Business Wealth S.E':
    r_simple     = r_simple * float(busEpsScalar) + float(alphaBus)
    #  The check for abs(r) > 1 makes sense for simple returns, if r was log returns, this check would be different
  if np.any(np.abs(r_simple) > 1):
    violators = r_simple[np.abs(r_simple) > 1]
    indices = np.where(np.abs(r_simple) > 1)[0]
    print(f"DEBUG CRASH for {ticker}: Found {len(violators)} violations.")
    print(f"First 5 violating returns: {violators[:5]}")
    print(f"At array indices: {indices[:5]}")
    # raise RuntimeError(f"{ticker} produced non-return values, {np.abs(r_simple)}")
    print(f"{ticker} produced non-return values, {np.abs(r_simple)}, max{max(np.abs(r_simple))}")
    r_simple = np.clip(r_simple, -0.99, 1.0)
  
    # p (price path) reconstruction if needed downstream:
  if isinstance(firstP, pd.Series):
    firstP = float(firstP.iloc[0])



  elif isinstance(firstP, pd.DataFrame):
    firstP = float(firstP.iloc[0, 0])
  else:
    firstP = float(firstP)
  
  # cumR = np.exp(np.cumsum(r)) - 1
  cumR = np.cumprod(1 + r_simple) - 1
  explode_test(1000000, cumR, f"{ticker} in runassetSimul")
  p = firstP * np.exp(np.cumsum(r))
  # p = firstP * np.cumprod(1 + r)
  areDeposit = False



  

  if debug2 == True or debug2 == True:
    print(f"In runAssetSimul, {ticker} (Yahoo) r = {r}, cumR, p, sigma, fitSigma, time, areDeposit = ", cumR, p, sigma, fitSigma, time, areDeposit)
  if debug10 == True or debugBus == True:
    print(f"In runAssetSimul, {ticker}[:50] (Yahoo) r = {r[:50]}, cumR, p, sigma, fitSigma, time, areDeposit = ", cumR[:50], p[:50], sigma[:50], fitSigma[:50], time[:50], areDeposit)
  if debug10 == True  or debugBus == True:
    print(f"In runAssetSimul, {ticker} (means) (Yahoo) r mean = {np.nanmean(r)}, eps {np.nanmean(eps)} cumR, p, sigma, fitSigma, time, areDeposit = {np.nanmean(cumR)}, **p** {np.nanmean(p)}, SIGMA {np.nanmean(sigma)}, ***FIT SIGMA {np.nanmean(fitSigma)}, {time[:30]}, {areDeposit}")

  return(r_simple, cumR, p, sigma, fitSigma, time, areDeposit)







#
# r[t] = mu + eps[t]


# eps[t] = sigma[t] * z[t]


# sigma[t]**2 = omega + alpha1 * eps[t-1]**2 + beta * sigma[t-1]**2


# r, cumR, p, sigma, fitSigma, time, areDeposit = run_monteCarlo(assets["Equities"]['^STOXX'])


# print(r)


import os
# folder = r"C:\Users\eogha\OneDrive\Desktop\BT_Plots"










def getGraphs(time, r, cumR, portFitSigma, portSigma, title, areDeposit):
  x = pd.to_datetime(time)
  print(f"shape / type of x (time), {x.shape}, {type(x)}")




  plt.xlabel = matplotlib.pyplot.xlabel
  plt.ylabel = matplotlib.pyplot.ylabel
  if isinstance(r, list):
    for p in r:
      plt.plot(x, p, alpha=alpha)
  else:
    plt.plot(x, r)
  plt.title(f"Simulated {title} Return %")
  plt.xlabel("Date")
  plt.ylabel("Simulated Return %")
  plt.savefig(os.path.join(folder, "Simulated_Ret_Pct.png"), dpi=300)
  plt.show()




  if isinstance(cumR, list):
    for p in cumR:
      plt.plot(x, p, alpha=alpha)
  else:
    plt.plot(x, cumR)
  plt.title(f"Simulated {title} Return")
  plt.xlabel("Date")
  plt.ylabel("Simulated Cumulative Returns")
  plt.savefig(os.path.join(folder, "Simulated_Cum_Ret.png"), dpi=300)
  plt.show()




  #______Historical vs simulated volatility____
  #gaurd - ensuring arrays are  proper len
  if portSigma is not None and portFitSigma is not None and 3 == 2:
    portFitSigma = np.asarray(portFitSigma)


    if portFitSigma.size == 0:
      print("Woah hang on, fit sigma array is empty!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
      histVol = np.array([])
    else:
      histVol = portFitSigma[-500:]


    simHorizon = 300


    if isinstance(portSigma, list):
      for p in portSigma:
        if p.size == 0:
          print("Woah hang on, sim sigma array is empty!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
          futureVol = np.array([])
        else:
          futureVol = p[:simHorizon]


        if len(histVol) == 0:
          print("HistVol = Empty")
        else:
          histIndex = x[-len(histVol):]
          plt.plot(histIndex, histVol, alpha=alpha) # , label=f"Historical {title} GARCH Volatility"
          plt.xlabel("Date")
          plt.ylabel("Volatility")




        if len(futureVol) > 0:
          futureStart = x[-1] + pd.Timedelta(days=1)
          futureIndex = pd.date_range(start=futureStart, periods=len(futureVol), freq='B')
          plt.plot(futureIndex, futureVol) # , label=f"Simulated {title} Future Volatility"


    else:
      portSigma = np.asarray(portSigma)


      if portSigma.size == 0:
        print("Woah hang on, sim sigma array is empty!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        futureVol = np.array([])
      else:
        futureVol = portSigma[:simHorizon]


      if len(histVol) == 0:
        print("HistVol = Empty")
      else:
        histIndex = x[-len(histVol):]
        plt.plot(histIndex, histVol) # label=f"Historical {title} GARCH Volatility"
        plt.xlabel("Date")
        plt.ylabel("Volatility")




      if len(futureVol) > 0:
        futureStart = x[-1] + pd.Timedelta(days=1)
        futureIndex = pd.date_range(start=futureStart, periods=len(futureVol), freq='B')
        plt.plot(futureIndex, futureVol) # , label=f"Simulated {title} Future Volatility"
    plt.title(f"Historical vs Simulated {title} Volatility")
    plt.xticks(rotation=45)
    plt.savefig(os.path.join(folder, "Vol_Comparision2.png"), dpi=300)
    # plt.legend()
    plt.show()






#________Actually running multiple assets in portfolio__________
# ______________ Actual Monte Carlo run _______



def applyCorrelationModifer(
      fullCorr,
      allTickersOrdered,
      assets,
      inputParameters):
  
  tickerToClass = {}
  for assetClass, tickers in assets.items():
    for ticker in tickers:
        tickerToClass[ticker] = assetClass
  mode = inputParameters["Correlation Modifier"]["Mode"]
  fullCorrInitial = fullCorr.copy()
  fullCorr = fullCorrInitial.copy()
  n = fullCorr.shape[0]
  if mode == "Global":
    scalar = inputParameters["Correlation Modifier"]["Global Scalar"]
    if useBlending:
        if scalar < 1.0:
            # Decrease correlation: Blend towards Identity Matrix (0 correlation)
            weight = 1.0 - scalar  # e.g., 0.9 scalar means 10% weight towards Identity
            target_matrix = np.eye(n)
            fullCorr = (1.0 - weight) * fullCorr + weight * target_matrix
            
        elif scalar > 1.0:
            # Increase correlation: Blend towards Matrix of 1s (perfect correlation)
            weight = scalar - 1.0  # e.g., 1.1 scalar means 10% weight towards Perfect
            weight = min(weight, 0.99) #
            target_matrix = np.ones((n, n))
            fullCorr = (1.0 - weight) * fullCorr + weight * target_matrix
    else:
        scalar = inputParameters["Correlation Modifier"]["Global Scalar"]
        mask = ~np.eye(fullCorr.shape[0], dtype=bool)

        fullCorr[mask] *= scalar 
  elif mode == "AssetClass" or mode == "assetClass":
    blah = 1
    # fullCorr = fullCorrInitial
    try:
      for i, ticker_i in enumerate(allTickersOrdered):
        for j, ticker_j in enumerate(allTickersOrdered):
            class_i = tickerToClass[ticker_i]
            class_i_modifer = inputParameters["Correlation Modifier"]["assetClassScalars"].get(class_i, 1.0)

            class_j = tickerToClass[ticker_j]
            class_j_modifer = inputParameters["Correlation Modifier"]["assetClassScalars"].get(class_j, 1.0)
            # modifer = max(class_j_modifer, class_i_modifer) / 2
            modifier = (
                class_i_modifer +
                class_j_modifer
            ) / 2
            fullCorr[i, j] *= modifier
    except Exception:
       raise Exception
  # fullCorr = np.clip(fullCorr, -0.999, 0.999)
  mask = ~np.eye(fullCorr.shape[0], dtype=bool)

  fullCorr[mask] = np.clip(
      fullCorr[mask],
      -0.999,
      0.999
  )
  eigvals = np.linalg.eigvalsh(fullCorr)

  if np.min(eigvals.real) < 0:
      if debugCorrelation:
        print("Before repair:")
        print("Mean corr =", np.mean(fullCorr[np.triu_indices_from(fullCorr,1)]))
        print("Min eig =", np.linalg.eigvalsh(fullCorr).min())
      shift = -np.min(eigvals.real) + 1e-6
      fullCorr += (shift) * np.eye(fullCorr.shape[0])
      d = 1.0 / np.sqrt(np.diag(fullCorr))
      fullCorr = fullCorr * np.outer(d, d)
      if debugCorrelation:
        print("In applyCorrelationModifer:")
        print("After repair:")
        print("Mean corr =", np.mean(fullCorr[np.triu_indices_from(fullCorr,1)]))
        print("Min eig =", np.linalg.eigvalsh(fullCorr).min())
        print("Repair shift =", shift)
        if mode == "Global":
           print(f"HEY: scalar is {scalar}, globally applied.")
        assert np.allclose(np.diag(fullCorr), 1.0, atol=1e-10
    )
  # np.fill_diagonal(fullCorr, 1.0)
  # print("\nScenario:", scenario_name)
  if debugCorrelation:
      print("In applyCorrelationModifer:")
      print(
          "Mean corr:",
          np.mean(fullCorr[np.triu_indices_from(fullCorr, k=1)])
      )

      print(
          "Min eigenvalue:",
          np.linalg.eigvalsh(fullCorr).min()
      )
      print("Mean corr:",
      np.mean(fullCorr[np.triu_indices_from(fullCorr,1)]))

      print("Min corr:", np.min(fullCorr))
      print("Max corr:", np.max(fullCorr))

      # print("Min eig:", np.linalg.eigvalsh(fullCorr).min())
  return fullCorr


  


def runPort(
    coeffsDict, assetWeights, fullCorr, allTickersOrdered, assetsCompleted, corrAbleClasses, assetsYahoo,
    assets, households, time, returnsDict, inputParameters, chunk_idx=None, master_seed=None, path_num=None, busEpsScalar=1.1, alphaBus=None, df_t=None, useCholesky=False):

  def _addHouseholdsZeros(portRet):
    for household in assetWeights:
      if household not in portRet:
        portRet[household] = np.zeros(len(time))
    return portRet


  def _addHouseholdsEmpty(portRet):
    for household in assetWeights:
      if household not in portRet:
        portRet[household] = []
    return portRet


  def _addHouseholdsEmptyDict(portRet):
    for household in assetWeights:
      if household not in portRet:
        portRet[household] = {}
    return portRet

  
  portRet = {}
  portCumR = {}
  portSigma = {}
  portFitSigma = {}
  portRet = _addHouseholdsZeros(portRet)
  portCumR = _addHouseholdsZeros(portCumR)
  portSigma = _addHouseholdsZeros(portSigma)
  portFitSigma = _addHouseholdsZeros(portFitSigma)
  zTotal = []
  zMeans = []
  zStds = []
  assetLevelZ = []
  classLevelZmeans = []
  commonZ = np.random.normal(loc=0.0, scale=1, size=len(time))


  assetReturnPaths = {} #asset class, ticker -> r_t
  assetSigmaPaths = {}






  for household in assetWeights:
    assetReturnPaths[household] = {}
    for assetClass in assetsCompleted:
      assetReturnPaths[household][assetClass] = {}
      for asset in assetsCompleted[assetClass]:
        assetReturnPaths[household][assetClass][asset] = {}
  for household in assetWeights:
    assetSigmaPaths[household] = {}
    for assetClass in assetsCompleted:
      assetSigmaPaths[household][assetClass] = {}
      for asset in assetsCompleted[assetClass]:
        assetSigmaPaths[household][assetClass][asset] = {}


  
  if master_seed == None:
     master_seed = 42
  path_id = path_num + chunk_idx
  local_seed = path_id + master_seed
  rng = np.random.default_rng(local_seed)
  if debugCorrelation:
    print(f"In path {path_id}, local seed is {local_seed}")
    print("fullCorr.shape", fullCorr.shape)
    print("len(allTickersOrdered", len(allTickersOrdered))
    assert fullCorr.shape[0] == len(allTickersOrdered)

  

  if useCholesky:
      L = np.linalg.cholesky(fullCorr)
      nAssets = L.shape[0]
      uncorrZ = rng.normal(0, 1, size=(nAssets, (len(time))))

        
      if debug2 == True:
        print("uncorrZ is ", uncorrZ)
      # uncorrZ = studentT.rvs(df=4, size=len(time))
      # print("L shape", L.shape, "uncorrZ", uncorrZ.shape)
      zCorrelated = L @ uncorrZ
  else:
          
      # =======================================
      #  RUNNING STUDENT T COPULA 
      # ======================================
      nAssets = fullCorr.shape[0]
      if df_t == None:
          df_t = 5 # finance norm 
      # df_t = df_t # degrees of freedom (lower = fat tail, more crashes)
      if debugCorrelation:
        print(f"in runPort, just before mv_t_samples, np.diag(fullCorr) {np.diag(fullCorr)}")
        print("Avg corr:", np.mean(fullCorr[np.triu_indices_from(fullCorr, 1)])
)

        print(
            "First eigenvalues:", np.sort(np.linalg.eigvalsh(fullCorr))[:5]
        )
      # Generating multivariate student-t samples from correlation matrix
      # mv_t_samples = multivariate_t.rvs(loc=np.zeros(nAssets), shape=fullCorr, df=df_t, size=len(time), random_state=local_seed).T # transposed => nassets, len(time)
      uncorrZ = rng.normal(0, 1, size=(nAssets, (len(time))))
      w_chi2 = rng.chisquare(df_t, size=len(time)) # manually generating chi-square distrubution for common rng
      L = np.linalg.cholesky(fullCorr)
      z_corr = L @ uncorrZ
      mv_t_samples = z_corr * np.sqrt(df_t / w_chi2)
      if debugCorrelation:
        sample_corr = np.corrcoef(mv_t_samples)

        print(
              "Sample corr mean (mv t samples):",
              np.mean(
                  sample_corr[
                      np.triu_indices_from(sample_corr, k=1)
                  ]
              )
          )
        

      u_samples = studentT.cdf(mv_t_samples, df=df_t) # convert to Uniform(0,1) with univariate Studet-t CDF


      zCorrelated = norm.ppf(u_samples) # convert to standard normal N(0,1) marginals using normap ppf. Hence, now Garch shocks with heavy-tail dependence.
  # Prevent absolute extremes (e.g., infinity) from floating point rounding
  zCorrelated = np.clip(zCorrelated, -8.0, 8.0)
  if debugCorrelation:
    sample_corr_z = np.corrcoef(zCorrelated)
    print(
          "Sample corr mean (zCorrelated):",
          np.mean(
              sample_corr_z[
                  np.triu_indices_from(sample_corr_z, k=1)
              ]
          )
      )
  if debug2 == True:
    print("zCorrelated is ", zCorrelated)
  assetId = 0
  df_zCorrelated = pd.DataFrame(zCorrelated, index=allTickersOrdered)
  try:
    if debugVol3 or debugCorrelation or debug4:
      print(f"zCorrelated shape: {zCorrelated.shape}")
      print(f"Mean correlation of zCorrelated: {np.nanmean(np.corrcoef(zCorrelated))}")
      print(f"Std of zCorrelated across paths: {np.nanstd(zCorrelated, axis=1).mean()}")#
  except:
    print("if debugVol3 or debugCorrelation or debug4: failed")

  if debugCorrelation:
    print("zCorrelated overall mean", np.mean(zCorrelated))
    print("zCorrelated overall std", np.std(zCorrelated))

    per_asset_mean = np.mean(zCorrelated, axis=1)
    per_asset_std = np.std(zCorrelated, axis=1)

    print("asset mean range",
          per_asset_mean.min(),
          per_asset_mean.max())

    print("asset std range",
          per_asset_std.min(),
          per_asset_std.max())
  
  for assetClass in assets:
    if assetClass in assetsYahoo or assetClass in assetsCompleted:
      if debug == True:
        print("std of mean of assetLevelZ is ", np.nanstd(np.nanmean(assetLevelZ)))
        print("std of assetLevelZs", np.nanstd(assetLevelZ))
      # classLevelZmeans.append(assetLevelZ)
      assetLevelZ = []
      if debug == True:
        print("Current std of means of Z means is ", np.nanstd(np.nanmean(zMeans)))
      for ticker in assets[assetClass]:
         if (ticker in assetsYahoo.get(assetClass, []) or ticker in assetsCompleted.get(assetClass, [])):




          # z = 0.8 * commonZ + 0.2 * np.random.normal(loc=0.0, scale=1, size=len(time))
          # z = (z - np.nanmean(z)) / np.nanstd(z)
          if debug == True:
            print("WOOO zCorrelated SHAPE ", zCorrelated.shape)
            print(assetId)
          # if ticker in df_zCorrelated.index:
          #     z = df_zCorrelated.loc[ticker].values[:len(time)]
          # else:
          #     print(f"Warning: {ticker} fallback to independent noise.")
          #     z = np.random.normal(0, 1, size=len(time))
          if (df_zCorrelated is not None and ticker in df_zCorrelated.index):
                z = df_zCorrelated.loc[ticker].values[:len(time)]
                # chunk_idx, path_id
          else:
                z = rng.normal(0, 1, size=len(time))
                print(f"Warning: {ticker} fallback to independent noise.")
          # if assetId >= zCorrelated.shape[0]:
          #   print(f"asset {ticker}'s index {assetId} is out of bounds for correlated assets, so is probably property / deposits")
          #   # z = uncorrZ
          #   z = np.random.normal(0, 1, size=len(time))
          #   # z = zCorrelated[assetId + 1, : len(time)]


          # else:
          #   z = zCorrelated[assetId, : len(time)]
          #   if debug2 == True:
          #     print("z before runAssetSimul is ", z)
          #   assetId += 1
          # assetLevelZ.append(z)
          # zTotal.append(z)
          # zMeans.append(np.nanmean(z))
          # zStds.append(np.nanstd(z))
          if debug == True:
            print("Z mean = ", np.nanmean(z), "Z std is ", np.nanstd(z))
          if debug4 == True:
            if ticker == 'Land Other':
              print(f"z with {ticker} before runAssetSimul is: {z}")
            print(f"Just before runAssetSimul, ticker: {ticker}, assetClass: {assetClass}, z len {len(z)} z: {z}")
          r, cumR, p, sigma, fitSigma, t, areDeposit = runAssetSimul(ticker, z, coeffsDict, assetWeights, assets, time, rng=rng, busEpsScalar=busEpsScalar, alphaBus=alphaBus)
          if isinstance(r, pd.Series):
                r = r.values
          if isinstance(sigma, pd.Series):
              sigma = sigma.values
          if isinstance(fitSigma, pd.Series):
              fitSigma = fitSigma.values

          # Trim/pad to target length
          targetLen = len(time) 
          if len(r) > targetLen:
              r = r[:targetLen]
              sigma = sigma[:targetLen]
              fitSigma = fitSigma[:targetLen]
          elif len(r) < targetLen:
              pad_width = targetLen - len(r)
              r = np.pad(r, (0, pad_width), mode='edge')
              sigma = np.pad(sigma, (0, pad_width), mode='edge')
              fitSigma = np.pad(fitSigma, (0, pad_width), mode='edge')
          # bugCheckData.append(ticker, "r mean:", np.nanmean(r), "r std:", np.nanstd(r))
          if np.any(r > 0.5):

            print(f"HEY!!!!!!\n", "=" * 40, f"r for {ticker}, {assetClass} is crazy. Clipped to + 50%")
            print(f"  Maximum Daily Return Found: {np.max(r):.4%}")
            print(f"  Total days exceeding 50%: {np.sum(r > 0.5)} out of {len(r)}")

          r = np.clip(r, -0.50, 0.50)

          if debug == True:
            print("WOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO HERE NOW !!!!!!!!!!!!", ticker, "r mean:", np.nanmean(r), "r std:", np.nanstd(r))


    #___________________________________________________________________________________
          #Actually seperating portfolios based on income
    #-----------------------------------------------------------------------------------
          for household in assetWeights:


            if debug7 == True:
              print(f"in portRun, [portRet[household]] is {portRet[household]}, for {household}")
              print(f"in portRun, assetWeights[household][assetClass][ticker] is {assetWeights[household][assetClass][ticker]}, for {household}")
              print(f"in portRun, [np.array(r)] is {np.array(r)}, for {household}")
              print("portRet[household] shape / type, ", type(portRet[household]), getattr(portRet[household], 'shape', None))
              print("assetWeights[household][assetClass][ticker] shape / type, ", type(assetWeights[household][assetClass][ticker]), getattr(assetWeights[household][assetClass][ticker], 'shape', None))
              print("np.array(r) shape / type, ", type(np.array(r)), getattr(np.array(r), 'shape', None))
            adjustment2 = 2
            rarray = np.array(r)
            if rarray.ndim == 1:

              rarray = rarray[:len(r)]
            if rarray.ndim == 2:
              rarray = rarray[assetId-1, :len(r)]


            key = (assetClass, ticker)
            assert rarray.shape == portRet[household].shape, (f"Return length mismatch for {ticker}:"
                    f"{rarray.shape} vs {portRet[household].shape}")


              # returnsDict = {}
              # for assetClass in assets:
              #     returnsDict[assetClass] = {}
              #     for household in assetWeights:
              #       returnsDict[assetClass][household] = {}




            if not household in assetReturnPaths:
                assetReturnPaths[household] = {}
            if not assetClass in assetReturnPaths[household]:
                assetReturnPaths[household][assetClass] = {}
            if not ticker in assetReturnPaths[household][assetClass]:
              assetReturnPaths[household][assetClass][ticker] = {}


            assetReturnPaths[household][assetClass][ticker] = assetWeights[household][assetClass][ticker] * rarray.copy()
            assetSigmaPaths[household][assetClass][ticker] = sigma








            # for (key), r in assetReturnPaths.items():
            #   max = np.max(np.abs(r))
            #   if max > 1: #daily returns > 100%
            #     print(f"WOOOOOOOOO EXPLODING ASSET !!!!!! {ticker}, {assetClass}, max daily return = {max}, first 5, {r[:5]}, last 5, {r[-5:]}")
            #   if max > 0.5: #daily returns > 100%
            #     print(f"WOOOOOOOOO explode-prone ASSET !!!!!! {ticker}, {assetClass}, max daily return = {max}, first 5, {r[:5]}, last 5, {r[-5:]}")

            if debugVolatility2:
              print(
                ticker,
                "rarray", np.shape(rarray),
                "portRet", np.shape(portRet[household])
          )
            portRet[household] += assetWeights[household][assetClass][ticker] * rarray

            # portCumR += classWeights[assetClass] * assetWeightsHousehold[assetClass][ticker] * np.array(cumR)
            r = rarray




            # portCumR[household] = np.cumsum(portRet[household])
            portCumR[household] = np.cumprod(1 + portRet[household]) - 1


            if debug2 == True:
              print(f" in portRun, [portCumR[household]] = ", portCumR[household])
            returnsDict[assetClass][household][ticker] = r
            #fixing fitsigma
            targetLen = len(time) 
            datesIndex = pd.to_datetime(time) # target date index


            if isinstance(fitSigma, np.ndarray) != True:
              fitSigmaArray = np.array(fitSigma)
              if debug4 == True or debug12 == True:


                print(f"fitSigma is len ({ticker}, {len(fitSigma)}, {fitSigma}")
                print(f"fitSigma is , {fitSigmaArray}")



            if isinstance(fitSigma, pd.Series):
              fitSigmaArray = fitSigma.values
            elif isinstance(fitSigma, pd.DataFrame):
              fitSigmaArray = fitSigma.values.flatten()
            else:
              fitSigmaArray = np.asarray(fitSigma)

            # Now trim or pad to match targetLen
            if len(fitSigmaArray) > targetLen:
              # Trim if too long (take the last targetLen elements)
              fitSigmaArray = fitSigmaArray[-targetLen:]
            elif len(fitSigmaArray) < targetLen:
              # Pad if too short (repeat last value or use edge padding)
              pad_length = targetLen - len(fitSigmaArray)
              fitSigmaArray = np.pad(fitSigmaArray, (0, pad_length), mode='edge')
              # if len(fitSigmaArray) < targetLen:
              #   fitSigmaArray = np.pad(fitSigmaArray, (0, targetLen - len(fitSigmaArray)), mode='edge')
              # else:
              #   fitSigmaArray = fitSigmaArray[:targetLen]


              # fitSigmaAligned = fitSigma.reindex(datesIndex, method='ffill') #forward fill
              # fitSigmaArray = fitSigmaAligned.to_numpy()[:targetLen]


              # fitDates = pd.to_datetime(time[2:])
              # reIndexedFitSigma = fitSigma.reindex(fitDates)
              # fitSigma = reIndexedFitSigma.fillna(0)
              # portSigma += classWeights[assetClass] * assetWeights[assetClass][ticker] * np.array(sigma[2:])
              # portFitSigma += classWeights[assetClass] * assetWeights[assetClass][ticker] * np.array(fitSigma)
            # elif isinstance(fitSigma, np.ndarray) == True: #deposit
            #   fitSigmaArray = np.asarray(fitSigma)[:targetLen]
            simSigmaArray = np.asarray(sigma)[:targetLen]
            if len(simSigmaArray) > targetLen:
              simSigmaArray = simSigmaArray[:targetLen]
            elif len(simSigmaArray) < targetLen:
              pad_length = targetLen - len(simSigmaArray)
              simSigmaArray = np.pad(simSigmaArray, (0, pad_length), mode='edge')



            if len(simSigmaArray) < targetLen:
              if debug4 == True:
                print(f"(Mode edge) {ticker}, sigma = {sigma}, simSigmaArray= {simSigmaArray}")
              pad = targetLen - len(simSigmaArray)
              simSigmaArray = np.pad(simSigmaArray, (0, pad), mode='edge')
            elif len(simSigmaArray) > targetLen:
              simSigmaArray = simSigmaArray[:targetLen]



            if debugVolatility2:
              print(
                ticker,
                "simSigma", np.shape(simSigmaArray),
                "portSigma", np.shape(portSigma[household])
          )

            portSigma[household] += assetWeights[household][assetClass][ticker] * simSigmaArray


            portFitSigma[household] += assetWeights[household][assetClass][ticker] * fitSigmaArray
            # if debug7 == True:
            #   print("Final CumrR: ", cumR[-1])
            #   print("Final multiplier:", np.exp(cumR[-1]))
            #   print("CAGR:", np.exp(cumR[-1] / (len(time)/365)) - 1)
            #   for assetClass in portCumR:
            #     print(assetClass, np.exp(portCumR[assetClass][-1]) -1)


         else:
            print(f"Skipping asset {ticker} because not completed")
    # nt("Std of mean of classLevelZmeans ", np.nanstd(np.nanmean(classLevelZmeans)))


  tickers = []
  # retsList = [] #expected Return
  # for assetClass in returnsDict:
  #   for household in returnsDict[assetClass]:
  #     for ticker in returnsDict[assetClass][household]:
  #       tickers.append(ticker)
  #       retsList.append(returnsDict[assetClass][household][ticker])
  # retsArray = np.array(retsList) #sharpe: num tickers x num days






  #optimising for max Sharpe
  #sharpe = port mean / port std (risk free rate of 0)
  # print("MU = ", mu)




  riskPenalty = .6 #  weighting towards higher return.




  # newAllReturns = []
  # for assetClass in assets:
  #   for ticker in assets[assetClass]:
  #     series = np.asarray(returnsDict[assetClass][ticker], dtype=np.float64)
  #     newAllReturns.append(series)
  # # minLen = min(len(returnsDict[assetClass][ticker]) for assetClass in assets for ticker in assets[assetClass])
  # minLen = min(len(s) for s in newAllReturns)


  # allReturns = []
  # tickersLessDeposit = []
  # for assetClass in assets:
  #   if assetClass == "Deposit":
  #     continue
  #   elif assetClass != "Deposit":
  #     for ticker in assets[assetClass]:
  #       series = np.asarray(returnsDict[assetClass][ticker], dtype=np.float64)
  #       allReturns.append(series)
  #       tickersLessDeposit.append(ticker)




  # minLen = min(len(s) for s in allReturns)
  # retsMatrix = np.array([s[:minLen] for s in allReturns])


  # targetLen = len(time) - 2
  # retsList = []
  # muList = []
  # tickersLessDeposit = []
  # for assetClass in assets:
  #   for ticker in assets[assetClass]:


  #     r = np.asarray(returnsDict[assetClass][ticker], dtype=np.float64)
  #     if len(r) < targetLen:
  #       r = np.pad(r, (0, targetLen - len(r)), mode='edge')
  #     elif len(r) > targetLen:
  #       r = r[:targetLen]
  #     retsList.append(r)
  #     muList.append(r)
  #     tickersLessDeposit.append(ticker)


  retsList = {}
  retsList = _addHouseholdsEmpty(retsList)
  muList = {}
  muList = _addHouseholdsEmpty(muList)
  tickersLessDeposit = []
  for assetClass in assets:
    if assetClass == "Deposit":
      # series = np.full(len(time)-2, depositRate /252)
      # muVal = depositRate / 252
      # muList[household].append(muVal)
      print("Woah old deposit Logic !!!!!!!!! ")
    elif assetClass != "Deposit":
      for household in returnsDict[assetClass]:


        for ticker in returnsDict[assetClass][household]:
          series = np.asarray(returnsDict[assetClass][household][ticker], dtype=np.float64)
          retsList[household].append(series)
          muVal = np.nanmean(series)
          muList[household].append(muVal)
          tickersLessDeposit.append(ticker)




  # mu = np.array(muList)
  # houseWeights = []
  # for assetClass in assets:
  #   if assetClass == "Deposit":
  #     houseWeights.append(classWeightsHousehold['Deposit']['Deposit'])
  #   else:
  #     for ticker in assets[assetClass]:
  #       houseWeights.append(classWeightsHousehold[assetClass] * classWeightsHousehold[assetClass][ticker])
  # houseWeights = np.array(houseWeights)
  # optStd = np.sqrt(mc["optWeights"] @ mc["covMatrix"] @ mc["optWeights"])
  # houseStd = np.sqrt(houseWeights @ mc["covMatrix"] @ houseWeights)


  # minLen = min(len(s) for s in allReturns)
  retsMatrix = {
      household: np.vstack(retsList[household]) for household in retsList
      }
  mu = np.array(muList)
  if optRun == True:
    mu = np.array(muList)
    OptMu = mu * 252


# _______________________________________________Running optimal _______________________________________________________________________
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#=========================================================================================================================================






# #  numDays = retsMatrix.shape[1]
# #       depositReturns = np.full(numDays, depositRate / 252)
# #       retsMatrix = np.vstack([retsMatrix, depositReturns])
# #       mu = np.append(mu, depositRate/252)


#   depositReturns = np.full(retsMatrix.shape[1], depositRate / 252)
#   retsMatrix = np.vstack([retsMatrix, depositReturns])
#   # retsMatrix = np.array([returnsDict[assetClass][ticker][:minLen] for assetClass in assets for ticker in assets[assetClass]])
#   # retsMatrix = np.array([s[:minLen] for s in newAllReturns])


#   covMatrix = np.cov(retsMatrix, rowvar=True)
#   corrMatrix = np.corrcoef(retsMatrix)
#   if debug == True:
#     print("Correlations are ", corrMatrix)


#   OptcovMatrix = covMatrix * 252
#   riskFree = depositRate # Already daily rate
#   # muDaily = retsMatrix.mean(axis=1) / 100
#   # muSim = (1 + muDaily) ** 252 -1
#   # print("mu hist :", mu, "mu sim, ", muSim)


#   # print("optimiser mu (annual) = ", mu)
#   # muHist = np.array(np.nanmean([yf.download(ticker_symbol, start=start, end=end)['Close'].pct_change().dropna().mean() for assetClass in assets for ticker_symbol in assets[assetClass]]))
#   # mu = (1 + muHist) ** 252 -1




#   # longRunPremium = 0.06
#   # muHistAnnual = (1 + mu)*252 - 1
#   # shrinkage = 0.25 # 0 is all historical, 1 is all long run
#   # muShrunkAnnual = shrinkage * longRunPremium + (1 - shrinkage) * muHistAnnual
#   # mu = muShrunkAnnual




#   def negSharpe(weights):
#     portReturn = np.dot(weights, OptMu) # Annualized return
#     # Maximize return given the constrained risk, so objective is just return
#     return -(portReturn - riskFree * 252) # Use annualized risk-free rate




#   # w0 = np.ones(len(tickers)) / len(tickers) # intiial guess, all equal
#   # bounds = [(0,1) for _ in range(len(tickers))]


#   # mu = np.array(getMu(ticker) for assetClass in assets for ticker in assets[assetClass])
#   # mu = np.array([getMu(ticker_name) for ticker_name in tickers])






#   print("MUUUU", mu)
#   # tickers = tickersLessDeposit + ["Deposit"]
#   tickers = tickersLessDeposit + ["Deposit"]
#   w0 = np.ones(len(tickers)) / len(tickers) # intiial guess, all equal


#   bounds = [(0,1) for _ in range(len(tickers))]c
#   depIdx = tickers.index("Deposit")
#   bounds[depIdx] = (0, 0.2)


#   constraints = (
#       {'type':'eq', 'fun': lambda w: np.sum(w) - 1},
#       # {'type':'eq', 'fun': lambda w: np.sqrt(np.dot(w, OptcovMatrix @ w)) - household_port_std_annual}
#   )


#   # for t, ticker in enumerate(tickers) - 1:
#   #   print(ticker, "mu", mu[t], "std:", np.nanstd(retsMatrix[t]))
#   if debug == True:
#     print("Correlations are ", corrMatrix)
#   optimalResult = minimize(negSharpe, w0, bounds=bounds, constraints=constraints)
#   optWeights = optimalResult.x




#   #portfolio simulation with optimal weights
#   # portExpReturns = optWeights @ retsArray
#   dailyExpRets = np.dot(optWeights, retsMatrix)u
#   portExpReturns = dailyExpRets
#   portExpCumR = np.cumsum(portExpReturns)
#   portExpStd = np.sqrt(optWeights @ covMatrix @ optWeights)




#   portVaR5 = -np.percentile(portExpReturns, 5)
  if debug == True:

    print("Overall std of z means, ", np.nanstd(zMeans))
    print("Overall std of means of z means, ", np.nanstd(np.nanmean(zMeans)))
    print("Overall std of z stds, ", np.nanstd(zStds))


  if debug2 == True:
    print(f" in portRun, [portCumR] = ", portCumR)
  return {
      "portSigma": portSigma,
      "portFitSigma": portFitSigma,
      "portRet": portRet,
      "portCumR": portCumR,
      "returnsDict": returnsDict,
      #________________________Optimal being removed_______________________
      # if optRun == True:
      #   "optWeights": optWeights,
      #   "portExpReturns": portExpReturns,
      #   "portExpCumR": portExpCumR,
      #   "portExpStd": portExpStd,
      #   "portVaR5": portVaR5,
      #   "optWeighs": optWeights,
      #   "covMatrix": covMatrix,
      "portZmeans": zMeans,
      "portZSTDmeans": np.nanstd(1),
      "portZmeanofStd": np.nanmean(1),
      "portZTotal": zTotal,
      "portZTotalMean": np.nanmean(1),
      "tickers": tickers,
      "assetReturnPaths": assetReturnPaths,
      "assetSigmaPaths": assetSigmaPaths
          }





def runMonteCarloReal(N, sampleStep, coeffsDict, fullCorr, allTickersOrdered, assetWeights, assetsCompleted, assetsYahoo, corrAbleClasses, households, 
                      time, returnsDict, inputParameters, chunk_idx=None, busEpsScalar=1.1, alphaBus=None, master_seed=None):
  assets = assetsCompleted
  def _pathSummary(path):
    r = path["portRet"]
    summariesByHousehold = {}
    for householdKey, retArray in r.items():
        if retArray.size == 0:
            summariesByHousehold[householdKey] = {
                "mean": np.nan,
                "std": np.nan,
                "VaR5": np.nan,
                "cumEnd": np.nan
            }
        else:
            summariesByHousehold[householdKey] = {
                "mean": np.nanmean(retArray),
                "std": np.nanstd(retArray),
                "VaR5": -np.percentile(retArray, 5),
                "cumEnd": path["portCumR"][householdKey][-1],
                "annualMean": (1 + np.nanmean(retArray)) ** daysPerYear - np.nanmean(retArray),
                "Lifetime": (1 + np.nanmean(retArray)) ** (daysPerYear * 82) - np.nanmean(retArray)
            }
    return summariesByHousehold


  if optRun == True:
    def _optPathSummary(path):
      r = path["portExpReturns"]
      return {
          "mean": np.nanmean(r),
          "std": np.nanstd(r),
          "VaR5": -np.percentile(r, 5),
          "cumEnd": path["portCumR"][-1]
      }


  path = None
  summaries = [] # This will now be a list of dicts (one dict of summaries per household per path)
  samplePathsPortRet = []
  samplePathsPortCumR = []
  samplePathsPortSigma = []


  optSummaries = []
  optSamplePathsPortRet = []
  optSamplePathsPortCumR = []
  optWeights = []


  allPathsPortRet = []
  allPathsPortCumR = []
  allPathsPortSigma = []


  optAllPathsPortRet = []
  optAllPathsPortCumR = []


  allZmeans = []
  optAllZeams = []
  allZMeanofstds = []
  optAllStds = []
  allZtotal = []
  allZtotalMeans = []
  allAssetReturnPaths = []
  allAssetSigmaPaths = []
  portFitSigma = None
  useCholesky = inputParameters["Overall"]["useCholesky"]
  df_t = inputParameters["Overall"]["df_t"]

  for i in range(N):
    # print("--- DEBUGGING SHIFT ---")
    # print(f"time type: {type(time)}, length: {len(time)}")
    # print(f"First few elements of time: {time[:3] if hasattr(time, '__getitem__') else 'N/A'}")
    # print(f"returnsDict type: {type(returnsDict)}, length: {len(returnsDict)}")
    path = runPort(coeffsDict, assetWeights, fullCorr, allTickersOrdered, assetsCompleted, corrAbleClasses, assetsYahoo, assets, households, time, returnsDict, 
                   inputParameters, chunk_idx=chunk_idx, master_seed=master_seed, path_num=i, busEpsScalar=busEpsScalar, alphaBus=alphaBus, useCholesky=useCholesky, df_t=df_t)
    summaries.append(_pathSummary(path)) # Append dict of summaries
    allPathsPortCumR.append(path["portCumR"])
    if debug2 == True:
      print(f" in mc run {i}, just after path is run in runPort, [allPathsPortCumR] = ", allPathsPortCumR)
    allPathsPortRet.append(path["portRet"])
    allPathsPortSigma.append(path["portSigma"])
    allAssetReturnPaths.append(path["assetReturnPaths"])
    allAssetSigmaPaths.append(path["assetSigmaPaths"])
    portFitSigma = path['portFitSigma']
    if optRun == True:
      optSummaries.append(_optPathSummary(path))
      optAllPathsPortRet.append(path["portExpReturns"])
      optAllPathsPortCumR.append(path["portExpCumR"])
      optWeights.append(path["optWeights"])
    # allZmeans.append(path["portZmeans"])
    # allZMeanofstds.append(path["portZMeanofStd"])
    # allZtotal.append(path["portZTotal"])
    # allZtotalMeans.append(path["portZTotalMean"])
    print("______________________________________________________________________________________________-")
    print("Current run completed = ", i)


    if i % sampleStep == 0:
      samplePathsPortCumR.append(path["portCumR"])
      if debug2 == True:
        print(f" in mc run within aggregation, {i}, [samplePathsPortCumR] = ", samplePathsPortCumR)
      samplePathsPortRet.append(path["portRet"])
      samplePathsPortSigma.append(path["portSigma"])


      if optRun == True:
        optSamplePathsPortCumR.append(path["portExpCumR"])
        optSamplePathsPortRet.append(path["portExpReturns"])
    if debug2 == True:
      print(f" in mc run {i}, [samplePathsPortCumR] = ", samplePathsPortCumR)
  # Process household paths for mean calculation
  processed_allPathsPortRet = {h: [] for h in households}
  processed_allPathsPortCumR = {h: [] for h in households}
  processed_allPathsPortSigma = {h: [] for h in households}


  for path_dict_ret in allPathsPortRet:
      for household_key, ret_array in path_dict_ret.items():
          if household_key in processed_allPathsPortRet:
              processed_allPathsPortRet[household_key].append(ret_array)


  for path_dict_cumr in allPathsPortCumR:
      for household_key, cumr_array in path_dict_cumr.items():
          if household_key in processed_allPathsPortCumR:
              processed_allPathsPortCumR[household_key].append(cumr_array)


  for path_dict_sigma in allPathsPortSigma:
      for household_key, sigma_array in path_dict_sigma.items():
          if household_key in processed_allPathsPortSigma:
              processed_allPathsPortSigma[household_key].append(sigma_array)


  # Convert lists of arrays to 3D arrays for mean calculation (simulations, households, time_steps)
  # Then compute mean across simulations for each household
  meanPathRet = {h: np.nanmean(np.array(processed_allPathsPortRet[h]), axis=0) if processed_allPathsPortRet[h] else np.array([]) for h in households}
  meanPathCumR = {h: np.nanmean(np.array(processed_allPathsPortCumR[h]), axis=0) if processed_allPathsPortCumR[h] else np.array([]) for h in households}
  meanPathSigma = {h: np.nanmean(np.array(processed_allPathsPortSigma[h]), axis=0) if processed_allPathsPortSigma[h] else np.array([]) for h in households}


  if optRun == True:
    # Assuming optAllPathsPortCumR and optAllPathsPortRet are lists of arrays (not dicts per household)
    optPathsMatrixCumR = np.array(optAllPathsPortCumR)
    optPathsMatrixRet = np.array(optAllPathsPortRet)
    optMeanPathCumR = np.nanmean(optPathsMatrixCumR, axis=0)
    optMeanPathRet = np.nanmean(optPathsMatrixRet, axis=0)


  # houseWeights = []
  # for assetClass in assets:
  #   if assetClass == "Deposit":
  #     houseWeights.append(classWeightsHousehold['Deposit']['Deposit'])
  #   else:
  #     for ticker in assets[assetClass]:
  #       houseWeights.append(classWeightsHousehold[assetClass] * classWeightsHousehold[assetClass][ticker])
  # houseWeights = np.array(houseWeights)
  # optStd = np.sqrt(mc["optWeights"] @ mc["covMatrix"] @ mc["optWeights"])
  # houseStd = np.sqrt(houseWeights @ mc["covMatrix"] @ houseWeights)


  # tickerassets = path["tickers"]
  # df = pd.DataFrame({
  #     "Asset": tickerassets,
  #     "Optimal": optWeights,
  #     "Household": houseWeights
  # })
  # df['Difference'] = df["Optmial"] - df["Household"]
  # print(df)
  if debug2 == True:
    print(f" in mc finished , [samplePathsPortCumR] = ", samplePathsPortCumR)
  if path == None:
     path = {}
  return {
      "summaries": summaries,
      "samplePathsPortRet": samplePathsPortRet,
      "samplePathsPortCumR": samplePathsPortCumR,
      "samplePathsPortSigma": samplePathsPortSigma,
      "allPathsPortRet": allPathsPortRet,
      "allPathsPortCumR": allPathsPortCumR,
      "allPathsPortSigma": allPathsPortSigma,
      "meanPathCumR": meanPathCumR, # Now a dict of arrays
      "meanPathRet": meanPathRet,   # Now a dict of arrays
      "meanPathSigma": meanPathSigma, # Now a dict of arrays
      "portFitSigma": path.get("portFitSigma", None), # This will be a dict of arrays (last path's fitSigma)
      # "allZmeans": allZmeans,
      # "allZMeanofstds": allZMeanofstds,
      # "allZtotal": allZtotal,
      # "allZtotalMeans": allZtotalMeans,
      "allAssetReturnPaths": allAssetReturnPaths,
      "allAssetSigmaPaths": allAssetSigmaPaths
      # if optRun == True:
      #   "optSummaries": optSummaries,
      #   "optSamplePathsPortCumR": optSamplePathsPortCumR,
      #   "optSamplePathsPortRet": optSamplePathsPortRet,
      #   "optMeanPathCumR": np.array(optMeanPathCumR),
      #   "optMeanPathRet": np.array(optMeanPathRet),
      #   "optWeights": optWeights,


  }






# mc = runMonteCarloReal(N=200, sampleStep=1)

def runChunks(inputParameters, coeffsDict, fullCorr, allTickersOrdered, assetWeights, assets, assetsCompleted, assetsYahoo,
              corrAbleClasses, households,
              time, returnsDict, folder, V_num, busEpsScalar=1.1, alphaBus=None, testOneChunk=False, master_seed=None):
  stage = "runChunks"
  failed_count = 0

  totalPaths = inputParameters['Chunks']['totalPaths']#5000
  chunkSize = inputParameters['Chunks']['chunkSize']
  daysPerYear = inputParameters["Overall"]["daysPerYear"]
  busEpsScalar = inputParameters["Busniess Equity"]["busEpsScalar"]
  alphaBus = inputParameters["Busniess Equity"]["alphaBusRaw"] / daysPerYear
  samplePathsTarget = inputParameters["Overall"]["needed_graphs"]
  # samplePathsTarget = 150
  overAllResults = {}
  sampleStep = max(1, totalPaths // samplePathsTarget)

  debugChunk = True
  import copy
  import gc


  def _getChunkResult(mc):
    chunkResult = {
      "monteCarlo": {
          "sampleHouseholdRet": mc["samplePathsPortRet"],
          "sampleHouseholdCum": mc['samplePathsPortCumR'],
          "sampleHouseholdSigma": mc['samplePathsPortSigma'],
          # if optRun == True:
          #   "sampleOptRet": mc['optSamplePathsPortRet'],
          #   "sampleOptCum": mc['optSamplePathsPortCumR'],


          "allHouseholdRet": mc['allPathsPortRet'],
          "allHouseholdCum": mc['allPathsPortCumR'],
          "allHouseholdSigma": mc['allPathsPortSigma'],


          "meanHouseholdRet": mc['meanPathRet'], # This is now a dict
          "meanHouseholdCum": mc['meanPathCumR'], # This is now a dict
          "meanHouseholdSigma": mc['meanPathSigma'], # This is now a dict


          # if optRun == True:
          #   "meanOptRet": mc['optMeanPathRet'],
          #   "meanOptCum": mc['optMeanPathCumR'],


          "summaries": mc["summaries"],
          # if optRun == True:
          #   "optSummaries": mc['optSummaries'],
          "portFitSigma": mc["portFitSigma"],
          "allAssetReturnPaths": mc["allAssetReturnPaths"],
          "allAssetSigmaPaths": mc["allAssetSigmaPaths"]
      },


      "inputs": {
          "assets": assets,
          "returnsDict": returnsDict,
          "assetWeights": assetWeights,
          # if optRun == True:
          #   "optWeights": mc["optWeights"],
          # "classWeightHousehold": classWeightsHousehold,
          # "assetWeightHousehold": assetWeightsHousehold,
          "time": time,


        },
    }
    return(chunkResult)


  chunkFolder = os.path.join(folder, "chunkResults")
  os.makedirs(folder, exist_ok=True)
  os.makedirs(chunkFolder, exist_ok=True)
  print(f"folder made, {chunkFolder}")
  overAllResults = None


  import re


  existing_max = -1


  # for fname in os.listdir(chunkFolder):
  #     match = re.search(rf"Chunk_Results_{V_num}", fname) # _(\d+)_(\d+)\.pkl
  #     if match:
  #         end_idx = int(match.group(2))
  #         existing_max = max(existing_max, end_idx)
  prefix = f"Chunk_Results_{V_num}_"
  for fname in os.listdir(chunkFolder):
    if not fname.startswith(prefix):
        continue

    try:
        start, end = fname.replace(".pkl", "").split("_")[-2:]
        end = int(end)
        existing_max = max(existing_max, end)
    except:
        continue
    
  startBase = existing_max + 1

  # allPathsPortRet_global = []

  print(f"Continuing from path index {startBase}")
  for start in range(startBase, startBase + totalPaths, chunkSize):
    end = min(start + chunkSize, totalPaths)
    nChunk = end - start
    if debugChunk == True:
      print(f"Running Monte Carlo Chunk {start} to {end - 1}, {nChunk} paths")


    if nChunk == 0:
      # continue
      break
    
    chunk_idx = start 
    if master_seed == None:
       master_seed = 42
    # chunk_seed = master_seed + chunk_idx
    # np.random.seed(chunk_seed)

    # rng = np.random.default_rng(chunk_seed)
    # Z_chunk = rng.standard_normal(
    # (chunkSize, T, len(assetsCompleted))
# )
    try:
      chunkResData = runMonteCarloReal(
          N=nChunk, sampleStep=sampleStep, coeffsDict=coeffsDict, fullCorr=fullCorr, allTickersOrdered=allTickersOrdered, assetWeights=assetWeights,
          assetsCompleted=assetsCompleted, assetsYahoo=assetsYahoo, corrAbleClasses=corrAbleClasses,
          households=households, time=time, returnsDict=returnsDict, inputParameters=inputParameters, busEpsScalar=busEpsScalar, 
          alphaBus=alphaBus, chunk_idx=chunk_idx, master_seed=master_seed,)
    except ValueError as e:                                                                 #assetsCompleted, corrAbleClasses, households, time, returnsDict,
        print(f"ERROR in runMonteCarloReal at chunk {start}-{end}")
        print(f"Error: {e}")
        # Print where the error happened
        import traceback
        traceback.print_exc()
        raise
    # chunkResData = runMonteCarloReal(N=nChunk, sampleStep=4)
    chunkResult = _getChunkResult(chunkResData)
    # for h in households:
    maxAllowed = 1000000 # 1000,000
    maxFound = get_absolute_max(chunkResult["monteCarlo"]["allHouseholdCum"])
    location = find_value_location(chunkResult["monteCarlo"]["allHouseholdCum"], maxFound)
    assert maxFound < maxAllowed, (
        f"Error: returns have exploded. Max found {maxFound}, {location}"
    )
    chunkSave = {
        "chunkIndex": (start, start + nChunk - 1),
        "chunkResults": chunkResult
    }
    # allPathsPortRet_global.append(chunkResult['monteCarlo']['allHouseholdRet'])

    # saving to drive
    filePath = os.path.join(chunkFolder, f"Chunk_Results_{V_num}_{start}_{start+nChunk-1}.pkl")
    # os.makedirs(filePath, exist_ok=True)
    # filePath.parent.mkdir(parents=True, exist_ok=True)
    try:
        try:
            with zstd.open(filePath, "wb") as f:
              pickle.dump(chunkSave, f)
              if debugChunk == True:
                print(f"Chunk saved: {filePath}")
        except zstd.ZstdError:
            with open(filePath, "wb") as f:
              pickle.dump(chunkSave, f)
              if debugChunk == True:
                print(f"Chunk saved: {filePath}")
    except Exception as e:
        if hardCrash:
            raise e
        else:
            log_pipeline_failure(
                e,
                stage="run_chunks",
                V_num=V_num,
                fname=fname,
                message=f"failed to dump chunkSave to {filePath}"
            )
            continue
    del chunkResData, chunkResult, chunkSave
    gc.collect()

    convergencePoints = []#50, 100, 200, 300, 500, 700, 1000, 1500, 2000, 3000, 4000, 5000]
    
    if testOneChunk:
      print("DW, just debugging. Calm the ham broski")
      break
    for num in range(0, totalPaths, chunkSize):
      if num % (8 * chunkSize):
        convergencePoints.append(num)
    currentNum = (start + nChunk )
    if currentNum % (32 * chunkSize) == 0:


      for num in range(0, currentNum, chunkSize):
        if num % (4 * chunkSize):
          convergencePoints.append(num)

      # convergencePoints.append(currentNum)
    #   def check_drive_mounted(path="/content/drive/MyDrive"):
    #     if not os.path.exists(path):
    #         print("Drive disconnected — remounting...")

    #         drive.mount('/content/drive', force_remount=True)
    #   check_drive_mounted()
      # results = run_combined_analysis(
      #     chunk_folder    = data_dir / "chunkResults", #/content/drive/MyDrive/Young_Economist/chunkResults",
      #     coeffs_dict     = coeffsDict,
      #     assets_completed= assetsCompleted,
      #     asset_weights   = assetWeights,
      #     households      = households,
      #     time_hist       = time,
      #     V_num           = V_num,
      #     convergence_checkpoints = convergencePoints,
      #     save_folder     = data_dir / "graphs" #"/content/drive/MyDrive/Young_Economist/graphs",
      # )
      
  # Merge chunkResult into overAllResults safely
#   if overAllResults is None:
#       overAllResults = copy.deepcopy(chunkResult)
#   else:
#       for key in chunkResult:
#           val = chunkResult[key]


#           # Sub-dictionaries
#           if isinstance(val, dict):


#               if key not in overAllResults:
#                   overAllResults[key] = {}
#               for subkey, subval in val.items():
#                   if subkey in overAllResults[key]:
#                       existing = overAllResults[key][subkey]


#                       # Convert scalars to list
#                       if np.isscalar(existing):
#                           existing = [existing]
#                       if np.isscalar(subval):
#                           subval = [subval]


#                       # Convert 0-D arrays to 1-D arrays
#                       if isinstance(existing, np.ndarray) and existing.ndim == 0:
#                           existing = existing.reshape(1)
#                       if isinstance(subval, np.ndarray) and subval.ndim == 0:
#                           subval = subval.reshape(1)


#                       # Merge
#                       if isinstance(existing, np.ndarray) and isinstance(subval, np.ndarray):
#                           overAllResults[key][subkey] = np.concatenate([existing, subval], axis=0)
#                       elif isinstance(existing, list) and isinstance(subval, list):
#                           overAllResults[key][subkey].extend(subval)
#                       else:
#                           # Mixed types -> convert to list
#                           overAllResults[key][subkey] = list(existing) + list(subval)
#                   else:
#                       # New subkey
#                       if np.isscalar(subval):
#                           overAllResults[key][subkey] = [subval]
#                       else:
#                           overAllResults[key][subkey] = subval


#           # Lists
#           elif isinstance(val, list):
#               if key not in overAllResults:
#                   overAllResults[key] = []
#               overAllResults[key].extend(val)


#           # NumPy arrays
#           elif isinstance(val, np.ndarray):
#               if key not in overAllResults:
#                   overAllResults[key] = val
#               else:
#                   existing = overAllResults[key]
#                   if np.isscalar(existing):
#                       existing = np.array([existing])
#                   if val.ndim == 0:
#                       val = val.reshape(1)
#                   overAllResults[key] = np.concatenate([existing, val], axis=0)


#           # Scalars
#           else:
#               if key not in overAllResults:
#                   overAllResults[key] = [val]
#               else:
#                   existing = overAllResults[key]
#                   if isinstance(existing, list):
#                       existing.append(val)
#                       overAllResults[key] = existing
#                   else:
#                       overAllResults[key] = [existing, val]


#   del chunkResult
#   gc.collect()
# print(f"Finished Monte Carlo.")


# filePath = os.path.join(folder,"overAllResults2.pkl")
# with open(filePath, "wb") as f:
#   pickle.dump(overAllResults, f)
# print("Saved Sim Results")


# =============================================================================================================================================#                               Graphs =============================================================================================================================================# =============================================================================================================================================# =============================================================================================================================================# =============================================================================================================================================# =============================================================================================================================================# =============================================================================================================================================# =============================================================================================================================================
# # Collect all saved chunk files in order
# chunkFiles = sorted(
#     [f for f in os.listdir(chunkFolder) if f.endswith('.pkl')],
#     key=lambda f: int(f.split('_')[2])   # sort by start index
# )

# # accumulate weighted mean paths and sample paths across all chunks.
# # The strategy: keep a running sum of (mean path * nPaths) then divide by
# # total paths at the end. This gives the correct grand mean without loading
# # everything into memory simultaneously.

# portCumR_sum    = {h: None for h in households}   # running sum for mean
# portSigma_sum   = {h: None for h in households}
# portRet_sum     = {h: None for h in households}
# portSampleCum   = {h: [] for h in households}     # collect sample paths
# totalPathsLoaded = 0

# for fname in chunkFiles:
#     fpath = os.path.join(chunkFolder, fname)
#     with open(fpath, "rb") as f:
#         saved = pickle.load(f)

#     mc_chunk  = saved['chunkResults']['monteCarlo']
#     nInChunk  = len(mc_chunk['allHouseholdCum'])   # number of paths in chunk

#     for h in households:
#         # Mean path for this chunk (already averaged within the chunk)
#         mean_cum   = mc_chunk['meanHouseholdCum'][h]
#         mean_ret   = mc_chunk['meanHouseholdRet'][h]
#         mean_sigma = mc_chunk['meanHouseholdSigma'][h]

#         if portCumR_sum[h] is None:
#             # First chunk — initialise the accumulators
#             portCumR_sum[h]   = mean_cum   * nInChunk
#             portRet_sum[h]    = mean_ret   * nInChunk
#             portSigma_sum[h]  = mean_sigma * nInChunk
#         else:
#             portCumR_sum[h]  += mean_cum   * nInChunk
#             portRet_sum[h]   += mean_ret   * nInChunk
#             portSigma_sum[h] += mean_sigma * nInChunk

#         # Collect sample paths (these are individual paths for plotting)
#         for path in mc_chunk['sampleHouseholdCum']:
#             portSampleCum[h].append(path[h])

#     totalPathsLoaded += nInChunk
#     print(f"  Loaded chunk {fname}: {nInChunk} paths "
#           f"(total so far: {totalPathsLoaded})")

# # Divide accumulated sums by total paths to get the true grand mean
# portCumR  = {h: portCumR_sum[h]  / totalPathsLoaded for h in households}
# portRet   = {h: portRet_sum[h]   / totalPathsLoaded for h in households}
# portSigma = {h: portSigma_sum[h] / totalPathsLoaded for h in households}

# # Also need per-asset mean paths and sigma paths for attribution graphs.
# # These live in the asset-level state file you already load at the top.
# # fullSavedAssetRes already has 'meanAssetPath' and 'sigmaAssetPath'.

# # Build aggRes in the exact shape portfolioAggregation() would return,
# # so getGraphs() and everything downstream works unchanged.
# aggRes = {
#     "portCumR":      portCumR,
#     "portRet":       portRet,
#     "portSigma":     portSigma,
#     "portSampleCum": portSampleCum,
#     "summaryTable":  pd.DataFrame([
#         {
#             "Household":             h,
#             "Mean Cumulative Return": portCumR[h][-1],
#             "Mean Std Daily Return":  np.nanmean(portSigma[h]),
#             "Mean Daily Return":      np.nanmean(portRet[h]),
#         }
#         for h in households
#     ])
# }

# print(f"\nAggregation complete. Total paths: {totalPathsLoaded}")
# for h in households:
#     print(f"  [{h}] Final cumulative return: {portCumR[h][-1]:.2%}")

#=================
def monte_carlo_convergence_chunked(chunkFolder, households, pathCountsConverge):
    """
    Loads chunks one by one and records the cumulative mean return
    at each path count checkpoint. This tests convergence without
    needing all paths in memory.
    """
    import os, pickle
    import numpy as np
    import pandas as pd

    chunkFiles = sorted(
        [f for f in os.listdir(chunkFolder) if f.endswith('.pkl')],
        key=lambda f: int(f.split('_')[2])
    )

    # Running accumulators
    cumR_sum  = {h: None for h in households}
    totalSeen = 0
    records   = []
    checkpoints = set(pathCountsConverge)

    for fname in chunkFiles:
        fpath = os.path.join(chunkFolder, fname)
        try:
            try:
                with zstd.open(fpath, "rb") as f:
                    saved = pickle.load(f)
            except zstd.ZstdError:
                with open(fpath, "rb") as f:
                    saved = pickle.load(f)
        except Exception as e:
            print(f"Skipping corrupted chunk {fname}: {e}")
            continue
        # with open(fpath, "rb") as f:
        #     saved = pickle.load(f)

        mc_chunk  = saved['chunkResults']['monteCarlo']
        nInChunk  = len(mc_chunk['allHouseholdCum'])

        for h in households:
            mean_cum = mc_chunk['meanHouseholdCum'][h]  # shape: (nDays,)
            if cumR_sum[h] is None:
                cumR_sum[h] = mean_cum * nInChunk
            else:
                cumR_sum[h] += mean_cum * nInChunk

        totalSeen += nInChunk

        # Record at checkpoints
        if totalSeen in checkpoints or any(totalSeen >= c for c in checkpoints
                                           if c not in [r['Paths'] for r in records]):
            record = {'Paths': totalSeen}
            for h in households:
                grand_mean_final = (cumR_sum[h] / totalSeen)[-1]
                record[f'{h} Mean CumR'] = grand_mean_final
            records.append(record)
            print(f"  Checkpoint at {totalSeen} paths: "
                  f"{', '.join(f'{h}: {(cumR_sum[h]/totalSeen)[-1]:.2%}' for h in households)}")

        del saved
        gc.collect()

    return pd.DataFrame(records)



# 2. Build aggRes the normal way — this is fast, no Monte Carlo needed
# aggRes = portfolioAggregation(assetWeights)


# with open(os.path.join(folder, "aggRes_final.pkl"), "wb") as f:
#     pickle.dump(aggRes, f)
# print("saved")

# # getGraphs(aggRes)
# runGraphs(aggRes)

# 3. Load chunks only for things that need the full path distribution
#    i.e. backtest and convergence
# drive.mount('/content/drive', force_remount=True)

# allPathsPortRet = []
# chunkFiles = sorted(
#     [f for f in os.listdir(chunkFolder) if f.endswith('.pkl')],
#     key=lambda f: int(f.split('_')[2])
# )
# for fname in chunkFiles:
#     fpath = os.path.join(chunkFolder, fname)
#     with open(fpath, "rb") as f:
#         saved = pickle.load(f)
#     allPathsPortRet.extend(saved['chunkResults']['monteCarlo']['allHouseholdRet'])
#     del saved
#     gc.collect()

# # 4. Run graphs from aggRes (works immediately)
# getGraphs(aggRes)

# 5. Run backtest using the loaded paths

#(woo)







debugADC = False


import matplotlib.ticker as mtick
def getGraphs():
  folder = graph_dir #"/content/drive/MyDrive/Young_Economist/graphs"
  if not os.path.exists(folder):
    os.makedirs(folder)
    print("huh")
  graphFigSize = (14,6)
  alpha = 0.2
  titleWeight = 'normal'
  graphHeight = 14
  plt.rcParams.update({
      'font.family': 'DejaVu Sans',
      'font.size': 16,
      'axes.titlesize': 27,
  #title
      'axes.labelsize': 24,
      'xtick.labelsize': 16,
      'ytick.labelsize': 16,
      'legend.fontsize': 16,
      'legend.title_fontsize': 15,
      'figure.titlesize': 26,
      'axes.spines.top': False,
      'axes.spines.right': False,


      'axes.grid': True




    })


  householdDisplayLabels = {
      "0-20": "0–20th Income Percentile",
      "40-59": "40–59th Income Percentile",
      "80-100": "80–100th Income Percentile"
  }


  assetRes = aggRes
  assetClassColours = {
      "Equities": "tab:red",
      "Bonds Short": "tab:blue",
      "Bonds Long": "tab:purple",
      "Property": "tab:orange",
      "Deposits": "tab:green",
      "Business Wealth": "#FFD700"
  # "Equities", "Bonds Short": "tab:blue", "Bonds Long": "tab:purple", "Property": "tab:orange", "Deposits"
  }
  houseHoldAssetsColours = {
      "80-100": "tab:red",
      "0-20": "tab:blue",
      "40-59": "tab:green"
  }






  x = pd.to_datetime(time)
  plottingList = {}
  currentPath = []
  currentHousehold = []


  # for path in mc["sampleHouseholdCum"]:
  #   for household in path:
  #     print(f"Household == {household}")
  #     plottingList[household] = {}


  plottingList = {
      '80-100': {h: [] for h in households},
      '40-59': {h: [] for h in households},
      '0-20': {h: [] for h in households}
  }
  plottingList = {
      '80-100': [],
      '40-59': [],
      '0-20': []
  }
  minValue = {
      '80-100': 0,
      '40-59': 0,
      '0-20': 0
  }
  maxValue = {
      '80-100': 0,
      '40-59': 0,
      '0-20': 0
  }
  minList = {
      '80-100': [],
      '40-59': [],
      '0-20': []
  }
  maxList = {
      '80-100': [],
      '40-59': [],
      '0-20': []
  }


  houseHoldAssetsColours = {
      "80-100": "tab:red",
      "0-20": "blue",
      "40-59": "tab:green"
  }
  houseHoldAssetsColoursCumPaths = {
      "80-100": "crimson",
      "0-20": "mediumblue",
      "40-59": "green"
  }
  houseHoldAssetsColoursIntense = {
      "80-100": "deeppink",
      "0-20": "c",
      "40-59": "lime"
  }
  assetClassColours = {
      "Equities": "tab:red",
      "Bonds Short": "tab:blue",
      "Bonds Long": "tab:purple",
      "Property": "tab:orange",
      "Deposits": "tab:green",
      "Business Wealth": "#FFD700"
  # "Equities", "Bonds Short": "tab:blue", "Bonds Long": "tab:purple", "Property": "tab:orange", "Deposits"
  }


    # ================================================================================
  def makeTablePretty(df, name, folder, fontsize=16, col_width=4, row_height=1, header_color='darkslategray', row_colors=['lightgray', 'w'], edge_color='w'):


      # def smartRound(y, maxDec=7):
      #   x = y
      #   if pd.isnull(x):
      #     return ""
      #   if x == 0:
      #     return 0
      #   mag = -int(np.floor(np.log10(abs(x))))
      #   decimals = max(0, min(mag, maxDec))
      #   return round(x, decimals + 2)
      def smartRound(y):
        if pd.isnull(y):
            return ""
        if y == 0:
            return "0.00"
        if isinstance(y, (int, np.integer)):
            return str(y)
        
      
        return f"{y * 100:.3f}"


      dfRound = df.copy()
      for col in dfRound.select_dtypes(include=[np.number]):


      # numCol = dfRound.select_dtypes(include=['float', 'int']).columns
        dfRound[col] = dfRound[col].apply(smartRound)
      df = dfRound
      fig_width = col_width * len(df.columns)
      fig_height = row_height * (len(df)) + 1


      fig, ax = plt.subplots(figsize=(fig_width, fig_height))
      ax.axis('off')


      mpl_table = ax.table(
          cellText=df.values,
          colLabels=df.columns,
          cellLoc='center',
          loc='center'
      )
      mpl_table.scale(1, 1.5)
      plt.tight_layout(pad=0)
      # plt.subplots_adjust(top=1, bottom=0, left=0, right=1)
      plt.subplots_adjust(top=0.88, bottom=0.05)
      ax.set_position([0, 0, 1, 1])
      mpl_table.auto_set_font_size(False)
      mpl_table.set_fontsize(fontsize)


      # Color header
      for (i, j), cell in mpl_table.get_celld().items():
          if i == 0:
              cell.set_text_props(weight='bold', color='w')
              cell.set_facecolor(header_color)
          else:
              cell.set_facecolor(row_colors[i % len(row_colors)])
          cell.set_edgecolor(edge_color)




      saveName = name.replace(" ", "_")
      filename = f"{saveName}.png"
      plt.title(name)
      # plt.tight_layout()
      plt.savefig(os.path.join(folder, filename), dpi=600)
      plt.show()
      plt.close()




  def houseCumSampleWithSigmaBanded(time, graphFigSize, assetRes, households):
    x = pd.to_datetime(time[:])
    sampleSummaryRows = []
    # sigma bands removed
    plt.figure(figsize=graphFigSize)
    for h in households:
    #   upper = (assetRes['portCumR'][h] + assetRes['portSigma'][h])*100
    #   lower = (assetRes['portCumR'][h] - assetRes['portSigma'][h])*100
    #   plt.fill_between(x, lower, upper, color=houseHoldAssetsColoursIntense[h], alpha=1)
    #   plt.plot(x, upper, color=houseHoldAssetsColoursIntense[h], alpha=1, linewidth=4, linestyle='--')
    #   plt.plot(x, lower, color=houseHoldAssetsColoursIntense[h], alpha=1, linewidth=4, linestyle='--')
      for path in assetRes['portSampleCum'][h]:
        if h == '40-59':
          # alpha = alpha * 1.5
          plt.plot(x, path*100, color=houseHoldAssetsColoursCumPaths[h], alpha=(alpha*1.3), linewidth=0.8)




        else:
          plt.plot(x, path*100, color=houseHoldAssetsColoursCumPaths[h], alpha=alpha, linewidth=0.8)
        # plottingList[h].append(path[-1])
      # mean
      # plt.plot(x, assetRes['portCumR'][h]*100, color=houseHoldAssetsColoursIntense[h], label=householdDisplayLabels[h], linewidth=4)
      # print(plottingList[h])
      sampleSummaryRows.append({
          "Household": h,
          "Std of Paths Cumulative Return": np.nanstd(plottingList[h]),
          "Maximum Return": max(plottingList[h]),
          "Minimum Return": min(plottingList[h])
      })
      # sigma bands +/- 1, why not

    plt.plot([], [], label=f"{householdDisplayLabels['0-20']}") #B R G
    plt.plot([], [], label=f"{householdDisplayLabels['80-100']}")
    plt.plot([], [], label=f"{householdDisplayLabels['40-59']}")
    plt.title("Household Portfolio: Cumulative Return Paths", weight=titleWeight)
    plt.xlabel("Date")
    plt.ylabel("Cumulative Return (%)")
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(100.0))
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title="HH Income Group")
    plt.savefig(os.path.join(folder, "cumRpaths.png"), dpi=600)
    plt.show()
    # sampleSummary = pd.DataFrame(sampleSummaryRows)
    # makeTablePretty(sampleSummary, 'Sample Path Summary', folder)




  def householdVolatility():
    # x = pd.to_datetime(time)
    plt.figure(figsize=graphFigSize)
    for h in households:
      plt.plot(x, assetRes['portSigma'][h], label=f"{h} Household Volatility", color=houseHoldAssetsColours[h])
    plt.title("Household Daily Volatility Over Time")
    plt.xlabel("Time")
    plt.ylabel("Volatility")
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.legend(
          loc="upper right",
          fontsize=15,          # smaller font (half if original was ~12)
          title_fontsize=17,    # smaller title
          handlelength=1.5,      # shorter legend lines
          handleheight=1,    # shrink vertical size of handles
          labelspacing=.6     # reduce vertical spacing between labels
      )
    plt.grid(True)
    plt.savefig(os.path.join(folder, "householdVolatility.png"), dpi=600)
    plt.show()
  householdVolatility()
  def assetClassVolatilityBar():
    # x = pd.to_datetime(time)
    assetClassVolatility = {}
    plt.figure(figsize=graphFigSize)
    sigmaList = []
    colourList = []
    labelList = []
    for assetClass in fullSavedAssetResFull['sigmaAssetClassPath']:
      sigmaList.append(np.nanmean(fullSavedAssetResFull['sigmaAssetClassPath'][assetClass]))
      labelList.append(f"{assetClass}")
      colourList.append(assetClassColours[assetClass])
    # plt.bar(label=f"{assetClass}", color=assetClassColours[assetClass], alpha=alpha)
    plt.bar(labelList, sigmaList, color=colourList)
    plt.title(f"Mean Asset Class Volatility", weight=titleWeight)
    plt.xlabel("Asset Class")
    plt.xticks(labelList, rotation=35, ha='right' )
    plt.ylabel("Volatility")
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.legend(
          loc="upper right",
          fontsize=15,          # smaller font (half if original was ~12)
          title_fontsize=17,    # smaller title
          handlelength=1.5,      # shorter legend lines
          handleheight=1,    # shrink vertical size of handles
          labelspacing=.6     # reduce vertical spacing between labels
      )
    plt.grid(False)
    plt.savefig(os.path.join(folder, "assetClassVolBar.png"), dpi=600)
    plt.show()
  # assetClassVolatilityBar()


  def getHouseholdVolTable():
    houseVolatilityRows = []
    for h in households:
      sigma = aggRes['portSigma'][h]
      houseVolatilityRows.append({
              "Household": h,
              "Final Volatility": sigma[-1],
              "Mean Volatility": np.nanmean(sigma),
              "Std of Volatility": np.nanstd(sigma)
          })
    houseVolTable = pd.DataFrame(houseVolatilityRows)
    #sort
    houseVolTable = houseVolTable.sort_values(by=["Household"]).reset_index(drop=True)


    print("\n=== Household Volatility Summary ===")
    # print(houseVolTable)
    makeTablePretty(houseVolTable, 'Household Volatility Summary', folder)
  getHouseholdVolTable()


  def getAssetVolTable():
    assetVolatilityRows = []
    for assetClass in fullSavedAssetResFull['sigmaAssetClassPath']:
        sigma = fullSavedAssetResFull['sigmaAssetClassPath'][assetClass]
        assetVolatilityRows.append({
            "Asset Class": assetClass,
            "Final Volatility": sigma[-1],
            "Mean Volatility": np.nanmean(sigma),
            "Std of Volatility": np.nanstd(sigma)
          })
    assetVolTable = pd.DataFrame(assetVolatilityRows)
    #sort
    assetVolTable = assetVolTable.sort_values(by=["Asset Class"]).reset_index(drop=True)


    print("\n=== Asset Class Volatility Summary ===")
    makeTablePretty(assetVolTable, 'Asset Class Volatility Summary', folder)
  # getAssetVolTable()


  def meanHousePath():
    meanSummaryRows = []
    plt.figure(figsize= graphFigSize)
    finalVals = {h: 0 for h in households}
    for h in households:
      meanPath = aggRes['portCumR'][h]
      finalVals[h] = aggRes['portCumR'][h][-1]
      meanSummaryRows.append({
            "Household": h,
            "Final Return": finalVals[h],
            # "Std of Paths Cumulative Return": np.nanstd(finalVals[h]),
            # "Maximum Return": ,
            # "Minimum Return": min(plottingList[h])
        })


      plt.plot(x, meanPath, color=houseHoldAssetsColours[h], label=f"{householdDisplayLabels[h]}")



    plt.title("Cumulative Returns: Mean Household Path", weight=titleWeight)
    plt.xlabel("Date")
    plt.ylabel("Cumulative Return %")
    ax = plt.gca()
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.legend(
        [householdDisplayLabels[h] for h in households], title="HH Income Group")
    plt.legend(
      loc="upper left",
      fontsize=20,          # smaller font (half if original was ~12)
      title_fontsize=22,    # smaller title
      handlelength=2,      # shorter legend lines
      handleheight=1.5,    # shrink vertical size of handles
      labelspacing=.8     # reduce vertical spacing between labels
    )
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.savefig(os.path.join(folder, "meanPath.png"), dpi=600)
    plt.show()
    meanSummary = pd.DataFrame(meanSummaryRows)
    makeTablePretty(meanSummary, 'Mean Path Final Returns', folder)
    # print(finalVals)
  # meanHousePath()
  def summaryTableShow():
    summary = aggRes['summaryTable']
    makeTablePretty(summary, "Summary", folder, col_width=4)
  def callAllGraphs():


    meanHousePath()
    getHouseholdVolTable()
    getAssetVolTable()
    assetClassVolatilityBar()
    houseCumSampleWithSigmaBanded()
    summaryTableShow()
  callAllGraphs()
# =================================================================================================================================
#
# ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    =====
# ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    ====    =====


# =================================================================================================================================
# getGraphs()


def _streamline_results(full_output):
  item = {}
  
  # 1. Loop through top-level buckets: 'results', 'validation', etc.
  for category, analyses in full_output.items():
      if not isinstance(analyses, dict):
          continue
          
      # 2. Loop through analysis blocks: 'mean_household_results', 'house_vol_results', etc.
      for analysis_name, analysis_data in analyses.items():
          if isinstance(analysis_data, dict):
              
              # Check if 'raw' and bubble it up
              if 'raw' in analysis_data:
                  item[analysis_name] = analysis_data['raw']
              # elif 'core' in analysis_data:
                  # item[analysis_name] = analysis_data['core']
              else:
                  # Fallback: if there's no raw wrapper, just point to the dict itself
                  item[analysis_name] = analysis_data
                  
  return item

def is_numerical(obj):
  if isinstance(obj, np.ndarray):
    return np.issubdtype(obj.dtype, np.number)
  elif isinstance(obj, (list, tuple, set)):
    return len(obj) > 0 and all(isinstance(item, numbers.Number) for item in obj)
  else:
    return isinstance(obj, numbers.Number)
def _extract_general_metrics(metric_data, metric_config):
  """
  Accepts raw output from metric analysis. Looks up config profile in metric_config, runs targeted statsitical reductions
  (varying input shapes)
  """
  
  metric_data_local = copy.deepcopy(metric_data)
  metric_data_local = _streamline_results(metric_data_local)
  results = {bc: {} for bc in metric_data_local}

  def add_results(item, metrics_to_run, bc, domain, label, label2=None):
      if label not in results[bc]:
        results[bc][label] = {}
      if is_numerical(item):
         
        for m in metrics_to_run:

            if m == "raw":
              output = item
            else:
              if m in maths:
                output = float(maths[m](item))
            if label2 == None:
              results[bc].setdefault(label, {})[m] = output
            else:
              results[bc].setdefault(label, {}).setdefault(label2, {})[m] = output
      else:
        if label2 == None:
              results[bc].setdefault(label, {})["raw"] = item
        else:
          results[bc].setdefault(label, {}).setdefault(label2, {})["raw"] = item
        # results[bc][label][label2]["raw"] = output
      return results
  
  maths = {
      "mean": np.nanmean,
      "med": np.nanmedian,
      "std": np.nanstd,
      "p5": lambda x: np.nanpercentile(x, 5),
      "p95": lambda x: np.nanpercentile(x, 95),
      "len": np.size,
      "terminal": lambda x: x[-1] if hasattr(x, '__getitem__') else x

    }
  
  for broad_category, analysis_data in metric_data_local.items():
    bc = broad_category
    cfg = metric_config.get(broad_category, None)
    if cfg == None:
      print(f"Notice_me: {broad_category} within metric_data (local) is not in metric_config")
      continue

    target = cfg.get("target")
    structure = cfg.get("structure")
    domain = cfg.get("domain")
    metrics_to_run = cfg.get("metrics")

    # get raw data
    # data_raw = metric_data_local[broad_category].get("analysis_name")
    if isinstance(analysis_data, dict) and target in analysis_data:
      data = analysis_data.get(target)
    else:
      data = analysis_data
    
    #  if domain.lower() == "p":
    #   is_path_level = True
    # elif domain.lower() == "a":
    #   is_path_level = False
    # else:
    #   is_path_level = True
    #   print(f"Notice_me!!!! domain in {analysis_name}, {broad_category}, from metric_config, is neither p nor a. Weird")
    # ----------------
    # Shape proccesing
    # ----------------
    
    # elif structure == "nest_dict_s" and isinstance(structure, dict):
    if structure == "dict_arr_1" and isinstance(data, dict):
      for label, array in data.items():
        results = add_results(array, metrics_to_run, bc, domain, label)
        # for m in metrics_to_run:
        #   if m == "raw":
        #     output = array
        #   else:
        #     if m in maths:
        #       output = float(maths[m](array))
        #   results[bc][label][m] = output
    elif structure == "nest_dict_s" and isinstance(data, dict):
      for outer_key, inner_dict in data.items():
        for label, scalar_val in inner_dict.items():
          results = add_results(scalar_val, metrics_to_run, bc, domain, label, outer_key)
    elif structure == "dict_s" and isinstance(data, dict):
      for label, scalar_val in data.items():
         results = add_results(scalar_val, metrics_to_run, bc, domain, label)
    elif structure == "df" and isinstance(data, pd.DataFrame):
      # dataDict = data.to_dict(orient="index")
      for columnName, columnData in [(columnName, data[columnName]) for columnName in data]:
        results = add_results(columnData, metrics_to_run, bc, domain, columnName)
    elif structure == "l_dict_s" and isinstance(data, list):
        for index, inner_dict in enumerate(data):
            for label, scalar_val in inner_dict.items():
                # Uses array position index string as a subkey grouping identifier
                results = add_results(scalar_val, metrics_to_run, bc, domain, label, label2=f"idx_{index}")
   
  return results

def get_comparable_results(metric_results, name, inputParameters, metric_config, coeffsDict, sensitivity_results=None, sensitivtyParameters=None):
  if sensitivity_results == None:
    sensitivity_results = {}
  inputs = {
     "inputParameters": inputParameters,
     "sensitivtyParameters": sensitivtyParameters,
  }
  # path_level = {
  #    "back_tests": {
         
  #    }
  #    "wealth_gap_overall":
  #    "wealth_gap_asset_class":
  #    "returns":
  #    "risk":
     
  # }
  standardised_results = _extract_general_metrics(metric_results, metric_config)
  sensitivity_results[name] = {
    "inputs": inputs,
    # "summary": 
    "standardised_results": standardised_results,
    "coeffs_dict": coeffsDict,
    # "aggregate_level_results": 
    "full_results": metric_results
  }
    

   # wealth divergence
    # net 
      # test level
        #  wealth_gap_mean
        #  wealth_gap_median
        #  wealth_gap_p5
        #  wealth_gap_p95
        
        #  P(gap > 0)
        #  P(gap > 50)
      # path level
        # wealth_gap
    # asset_level
      # test level
        #  wealth_gap_asset_mean
        #  wealth_gap_asset_median
        #  wealth_gap_asset_p5
        #  wealth_gap_asset_p95
        
        #  P(gap > 0)
        #  P(gap > 50)
      # path level
        # wealth_asset_gap
  return sensitivity_results

# return {
#       "assetsCompleted": assetsCompleted, 
#       "assetsYahoo":assetsYahoo, 
#       "assets":assets, 
#       "assetWeights":assetWeights, 
#       "households": households, 
#       "time": time, 
#       "folder": folder,
#       "chunkFolder": chunkFolder, 
#       "fullSavedAssetRes": fullSavedAssetRes, 
#       "corrAbleClasses": corrAbleClasses, 
#       "metric_config": metric_config, 
#       "chunk_dir": chunk_dir, 
#       "graph_dir":graph_dir, 
#       "data_dir": data_dir, 
#       "scenarios": scenarios, 
#       "inputParameters": inputParameters}

def main(V_num, inputParameters=None, testOneChunk=False, comparable_results=None, metric_config=None, nPaths=None, chunkSize=None):
  
  stage = "main"
  failed_count = 0
  import traceback
#   !pip install stackprinter
  import stackprinter
  import time as tm

  
  try:
      print("=== SETUP ===")
      # if inputParameters == None:
      
      #   (
      #       assetsCompleted,
      #       assetsYahoo,
      #       assets,
      #       assetWeights,
      #       households,
      #       time,
      #       folder,
      #       chunkFolder,
      #       fullSavedAssetRes,
      #       corrAbleClasses,
      #       metric_config,
      #       chunk_dir,
      #       graph_dir,
      #       data_dir,
      #       scenarios,
      #       inputParameters


      #   ) = setup()
      # else:
      #    (
      #     assetsCompleted,
      #     assetsYahoo,
      #     assets,
      #     assetWeights,
      #     households,
      #     time,
      #     folder,
      #     chunkFolder,
      #     fullSavedAssetRes,
      #     corrAbleClasses
      # ) = setup()
      cfg = setup()
      if inputParameters is None:
        inputParameters = cfg["inputParameters"]
      if metric_config is None:
         metric_config = cfg["metric_config"]
  
  except Exception:
      print("FAILED IN SETUP")
      traceback.print_exc()
      stackprinter.show(style='lightbg')
      raise

  cfg = copy.deepcopy(cfg)
  if nPaths != None:
    cfg["inputParameters"]["Chunks"]["totalPaths"] = nPaths
  if chunkSize != None:
    cfg["inputParameters"]["Chunks"]["chunkSize"] = chunkSize
  # Step 2: getting data
  try:
        print("=== COEFF FITTING ===")
        coeffsDict, returnsDict, fullCorr, allTickersOrdered = getCoeffs(cfg["assets"], cfg["assetsCompleted"], cfg["assetsYahoo"], cfg["assetWeights"], cfg["households"], cfg["time"], cfg["corrAbleClasses"], {}, inputParameters)
        # returns_array = np.array(list(returnsDict.values()))
        # excessDays = np.sum(np.abs(returns_array) > 0.5)
        # total_days = len(returnsDict)
        # max_allowed_bad_days = total_days * 0.05  # 5% threshold

        # # Asserts that the count of excessDays is within limits
        # assert excessDays <= max_allowed_bad_days, (
        #     f"returnsDict has total days exceeding 50%: {excessDays} out of {total_days}"
        # )
        explode_test(3, returnsDict, "main() runChunks")
        print(f"RAM: (getCoeffs) {psutil.Process().memory_info().rss / 1024**3:.2f} GB"
)
        # assert np.any(np.abs(returnsDict) < 0.6), f"returnsDict has total days exceeding 50%: {np.sum(returnsDict.abs()) > 0.5)} out of {len(r)}"
  except Exception:
        print("FAILED IN GETCOEFFS")
        traceback.print_exc()
        stackprinter.show(style='lightbg')
        raise

  # Step 2: running baseline
  try:
    t0 = tm.perf_counter()
    print("=== CHUNK SIMULATION ===")
    # if debugLocal: V_num = "debug"
    aggres = runChunks(cfg["inputParameters"], coeffsDict, fullCorr, allTickersOrdered, cfg["assetWeights"], cfg["assets"], cfg["assetsCompleted"], cfg["assetsYahoo"], 
                       cfg["corrAbleClasses"], cfg["households"], cfg["time"], returnsDict, cfg["folder"], V_num, testOneChunk, master_seed=None)
    print(f"RAM: (aggres) {psutil.Process().memory_info().rss / 1024**3:.2f} GB"
)
  except Exception:
    print(f"FAILED IN RUN CHUNKS")
    traceback.print_exc()
    stackprinter.show(style='lightbg')
    raise

  # # Step
  # print("runChunk", tm.perf_counter()-t0)
  # try:
  #     print("=== BACKTESTS ===")
  #     if debugLocal != debugLocal:
  #       backtestResults = run_combined_analysis(
  #           chunk_folder=chunkFolder,
  #           coeffs_dict=coeffsDict,
  #           assets_completed=assetsCompleted,
  #           asset_weights=assetWeights,
  #           households=households,
  #           time_hist=time,
  #           V_num=V_num
  #       )

  # except Exception:
  #     print("FAILED IN BACKTESTS")
  #     traceback.print_exc()
  #     stackprinter.show(style='lightbg')
  #     raise


  try:
      print("=== ASSET AGGREGATION ===")

      assetResults = aggregate_to_asset_paths(
          nTotalPaths=inputParameters["Chunks"]["totalPaths"],
          V_num=V_num
      )
      print(f"RAM: (asset agg) {psutil.Process().memory_info().rss / 1024**3:.2f} GB"
)
  except Exception:
      print("FAILED IN ASSET AGGREGATION")
      traceback.print_exc()
      stackprinter.show(style='lightbg')
      raise


  try:
      print("=== PORTFOLIO AGGREGATION ===")

      aggRes = portfolioAggregation(
          assetWeights=cfg["assetWeights"],
          fullSavedAssetRes=assetResults,
          households=cfg["households"],
          assetsCompleted=cfg["assetsCompleted"]
      )
      print(f"RAM: (port agg) {psutil.Process().memory_info().rss / 1024**3:.2f} GB"
)

  except Exception:
      print("FAILED IN PORTFOLIO AGGREGATION")
      traceback.print_exc()
      stackprinter.show(style='lightbg')
      raise

      # runGraphs(aggRes, assetResults, time, households, graph_dir, metric_results, tablesNeeded=True, plots_to_generate=None):
  try:
      
      print("=== ANALYSIS ===")

      cache_file = Path(data_dir) / f"Aggregated_State_{V_num}.pkl"
      if cache_file.exists():
          print(f"Loading cached analysis: {cache_file}")

          with open(cache_file, "rb") as f:
              cached = pickle.load(f)

          aggRes = cached["aggRes"]
          assetResults = cached["assetResults"]
          metric_results = cached["metric_results"]
          # time = cached["time"]
          households = cached["households"]
          # comparable_results_new = cached["comparable_results_new"]
          cached_sr = cached.get("sensitivityResults", {})
          if scenarioName in cached_sr:
              sensitivityResults[scenarioName] = cached_sr[scenarioName]
          elif scenarioName in cached.get("comparable_results_new", {}):
              sensitivityResults[scenarioName] = cached["comparable_results_new"][scenarioName]
      else:
          metric_results = get_metric_analysis(
            chunk_folder=cfg["chunkFolder"],
            coeffs_dict=coeffsDict,
            assets_completed=cfg["assetsCompleted"],
            asset_weights=cfg["assetWeights"],
            households=cfg["households"],
            time_hist=cfg["time"],
            V_num=V_num,
            percentile_bands=inputParameters["percentile_bands"],
            aggRes = aggRes,  
            asset_level_res = assetResults

          )
          print(f"RAM: metric_results {psutil.Process().memory_info().rss / 1024**3:.2f} GB"
    )
          # print(f"WOOOOO results: {metric_results['results']['house_cum_results']['house_cum_df']}")
          comparable_results_new = get_comparable_results(
            metric_results=metric_results,
            name = "baseline", 
            inputParameters=inputParameters, 
            metric_config=metric_config,
            coeffsDict=coeffsDict,
            sensitivity_results=comparable_results)
          print(f"RAM: comparable results {psutil.Process().memory_info().rss / 1024**3:.2f} GB")
      
          print(f"baseline Chunk analysis complete. Saving to cache...")
          with open(cache_file, 'wb') as f:
              pickle.dump({
                  'aggRes': aggRes,
                  'assetResults': assetResults,
                  'metric_results': metric_results,
                  "comparable_results_new": comparable_results_new,
                  # 'time': time,
                  'households': cfg["households"]
              }, f)

  except Exception:
      print("FAILED ")
      traceback.print_exc()
      stackprinter.show(style='lightbg')
      raise
  try:
      print("=== GRAPHING ===")

      runGraphs(
          aggRes=aggRes,
          assetResults=assetResults,
          time=cfg["time"],
          households=cfg["households"],
          graph_dir=cfg["graph_dir"],
          metric_results=metric_results,
          tablesNeeded=True
      )
      print(f"RAM: graphing {psutil.Process().memory_info().rss / 1024**3:.2f} GB"
)

  except Exception:
      print("FAILED IN GRAPHING")
      traceback.print_exc()
      stackprinter.show(style='lightbg')
      raise

  _save_item(comparable_results_new, path=None, base_path=data_dir, add_to_base=f"comparable_results_{V_num}")
  return {
      "coeffsDict": coeffsDict,
      "returnsDict": returnsDict,
      "assetResults": assetResults,
      "portfolioResults": aggRes,
      "metricResults": metric_results,
      "comparable_results": comparable_results_new 
  }




#

       
          # if m in metrics_to_run
          # for m in metrics_to_run:
          #   if m == "raw":
          #     array = array
          #   else:
          #     if m in maths:
          #       output = float(maths[m](array))
          #       results[bc][outer_key][label][m] = output

   
   

#   # std, p5, p95, mean, median, mode, count, min, max,


def applyReturnShock(coeffsDict, muScalar=1.0, volScalar=1.0, target=None):
  # Returns modified copy of coeffsDict.
  # target is the assets to which the changes are applied (dict)
  # muScalar = 0.9 means 10% lower, same for vol
  import copy
  shocked = copy.deepcopy(coeffsDict)
  # if target is None:
    # target = {}
  for assetClass in shocked:
    for ticker in shocked[assetClass]:
      if not target or (assetClass in target and ticker in target):
        cd = shocked[assetClass][ticker]
        
        if 'mu' in cd and 'muHist' in cd:
          muInitial = cd.get('mu', None)
          
          muHistIntial = cd.get('muHist', None)
        
          if muInitial is None or muHistIntial is None: 
            print(f"mu initial for {ticker}, {assetClass} was {muInitial} in {applyReturnShock}.")
            continue
          # assert muHistIntial != None, f"mu hist initial for {ticker}, {assetClass} was {muHistIntial} in {applyReturnShock}."

          cd['muHist'] = muHistIntial * muScalar
          cd['mu'] = muInitial * muScalar

        #vol. bc sigma^2 = omega + alpha*eps^2 + beta*sigma^2, for sigma to be k times its size, omega*k^2 and alpha*k^2
        
        omega = cd.get('omega', None)
        if omega != None:
          cd['omega'] = omega * volScalar ** 2
        # alpha1 = cd.get('alpha1', None)
        # if alpha1 != None:
        #   cd['alpha1'] = alpha1 * volScalar ** 2
  return shocked





def flatten_results(comparable_results, drop_raw=True):
    """
    Flattens the comparable_results dictionary into a long-format Pandas DataFrame.
    
    Args:
        comparable_results (dict): The master dictionary returned by runSensitivityTests.
        drop_raw (bool): If True, skips 'raw' data keys to prevent massive arrays 
                         from cluttering the analytical DataFrame.
    """
    rows = []
    
    # 1. Loop through each scenario (e.g., 'baseline', 'LowerReturns10')
    for scenario_name, payload in comparable_results.items():
        
        # Extract scenario parameters for easy grouping 
        
        inputs = payload.get("inputs", {})
        params = inputs.get("sensitivtyParameters") or {} 
        
        param_type = params.get("type", "baseline")
        mu_scalar = params.get("muScalar", 1.0)
        vol_scalar = params.get("volScalar", 1.0)
        global_scalar = params.get("Global Scalar", np.nan)
        corr_mode = params.get("Mode", None)
        std_results = payload.get("standardised_results", {})
        df_t = params.get("df_t", np.nan)
        smallBlend = params.get("smallBlend", np.nan)
        largeBlend = params.get("largeBlend", np.nan)
        alphaBusRaw = params.get("alphaBusRaw", np.nan)
        busEpsScalar = params.get("busEpsScalar", np.nan)
        
        
        # 2. Traverse the metrics tree
        for category, level1_data in std_results.items():
            if not isinstance(level1_data, dict):
                continue
                
            for level1_key, level2_data in level1_data.items():
                if not isinstance(level2_data, dict):
                    continue
                    
                for level2_key, metric_data in level2_data.items():
                    
                    # 3A. If it's a dict, tis nested 2 levels deep (e.g., Household -> Asset -> Metric)
                    if isinstance(metric_data, dict):
                        for metric_name, value in metric_data.items():
                            if drop_raw and metric_name == "raw":
                                continue
                                
                            rows.append({
                                "Scenario": scenario_name,
                                "Type": param_type,
                                "muScalar": mu_scalar,
                                "volScalar": vol_scalar,
                                "Category": category,
                                "Level_1": level1_key,
                                "Level_2": level2_key,
                                "Metric": metric_name,
                                "Value": value,
                                "GlobalScalar": global_scalar,
                                "CorrMode": corr_mode,
                                "smallBlend": smallBlend,
                                "largeBlend": largeBlend,
                                "alphaBusRaw": alphaBusRaw,
                                "busEpsScalar": busEpsScalar,
                                "df_t": df_t
                            })
                    
                    # 3B. If it's a scalar, its hit the metric level early (e.g., Household -> Metric)
                    else:
                        if drop_raw and level2_key == "raw":
                            continue
                            
                        rows.append({
                            "Scenario": scenario_name,
                            "Type": param_type,
                            "muScalar": mu_scalar,
                            "volScalar": vol_scalar,
                            "Category": category,
                            "Level_1": level1_key,
                            "Level_2": None,          # Empty because there is no sub-asset
                            "Metric": level2_key,     # The key itself is the metric (e.g., 'mean')
                            "Value": metric_data,
                            "GlobalScalar": global_scalar,
                            "CorrMode": corr_mode,
                            "smallBlend": smallBlend,
                            "largeBlend": largeBlend,
                            "alphaBusRaw": alphaBusRaw,
                            "busEpsScalar": busEpsScalar,
                            "df_t": df_t
                        })
                        
    # Convert to DataFrame
    df = pd.DataFrame(rows)
    
    # Clean up any generic numpy types to standard floats where possible
    if 'Value' in df.columns:
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
        
    return df

def make_sensitivity_tables(comparable_df):

    def pull_metric(category, level1, metric, out_name):

        mask = (
            (comparable_df["Category"] == category)
            & (comparable_df["Level_1"] == level1)
            & (comparable_df["Metric"] == metric)
        )

        df = comparable_df.loc[
            mask,
            [
                "Scenario",
                "Type",
                "muScalar",
                "volScalar",
                "GlobalScalar",
                "CorrMode",
                "smallBlend",
                "largeBlend",
                "alphaBusRaw",
                "busEpsScalar",
                "df_t",
                "Value"
            ]
        ].copy()

        return df.rename(columns={"Value": out_name})

    poorName = '0-20'
    medName = '40-59'
    richName = '80-100'
    # -----------------------------
    # Core outputs
    # -----------------------------

    gap_df = pull_metric(
        "gap_results",
        "80-100 vs 0-20",
        "mean",
        "Gap"
    )

    rich_df = pull_metric(
        "mean_household_results",
        "80-100",
        "terminal",
        "RichTW"
    )

    middle_df = pull_metric(
        "mean_household_results",
        "40-59",
        "terminal",
        "MiddleTW"
    )

    poor_df = pull_metric(
        "mean_household_results",
        "0-20",
        "terminal",
        "PoorTW"
    )

    summary = (
        gap_df
        .merge(rich_df[["Scenario", "RichTW"]], on="Scenario")
        .merge(middle_df[["Scenario", "MiddleTW"]], on="Scenario")
        .merge(poor_df[["Scenario", "PoorTW"]], on="Scenario")
    )

    # -----------------------------
    # Baseline comparison
    # -----------------------------

    baseline = summary.loc[
        summary["Scenario"] == "baseline"
    ]

    if baseline.empty:
        print("Baseline scenario missing")

    baseline = baseline.iloc[0]

    for col in ["Gap", "RichTW", "MiddleTW", "PoorTW"]:

        baseline_val = baseline[col]

        summary[f"{col}_pct"] = (
            (summary[col] - baseline_val)
            /
            (
                0.5
                * (
                    np.abs(summary[col])
                    + np.abs(baseline_val)
                )
                + 1e-12
            )
        )

    pct_delta_input = np.where(
        summary["Type"] == "returns",
        summary["muScalar"] - 1.0,
        np.where(
            summary["Type"] == "volatility",
            summary["volScalar"] - 1.0,
            np.nan
        )
    )

    summary["GapElasticity"] = np.where(
        pct_delta_input != 0,
        summary["Gap_pct"] / pct_delta_input,
        np.nan
    )

    # ==========================================================
    # RETURNS
    # ==========================================================

    returns_table = summary[
        summary["Type"] == "returns"
    ][[
        "Scenario",
        "muScalar",
        "Gap_pct",
        "GapElasticity",
        "RichTW_pct",
        "MiddleTW_pct",
        "PoorTW_pct"
    ]].copy()

    returns_table = returns_table.rename(columns={
        "muScalar": "Return Scalar",
        "Gap_pct": "Gap %Δ",
        "GapElasticity": "Gap Elasticity",
        "RichTW_pct": f"{richName} TW %Δ",
        "MiddleTW_pct": f"{medName} TW %Δ",
        "PoorTW_pct": f"{poorName} TW %Δ"
    })

    _make_table_pretty(
        returns_table,
        "Return Sensitivity",
        graph_dir
    )

    # ==========================================================
    # VOLATILITY
    # ==========================================================

    vol_table = summary[
        summary["Type"] == "volatility"
    ][[
        "Scenario",
        "volScalar",
        "Gap_pct",
        "GapElasticity",
        "RichTW_pct",
        "MiddleTW_pct",
        "PoorTW_pct"
    ]].copy()

    vol_table = vol_table.rename(columns={
        "volScalar": "Vol Scalar",
        "Gap_pct": "Gap %Δ",
        "GapElasticity": "Gap Elasticity",
        "RichTW_pct": f"{richName} TW %Δ",
        "MiddleTW_pct": f"{medName} TW %Δ",
        "PoorTW_pct": f"{poorName} TW %Δ"
    })

    _make_table_pretty(
        vol_table,
        "Volatility Sensitivity",
        graph_dir
    )

    # ==========================================================
    # CORRELATION
    # ==========================================================

    corr_table = summary[
        summary["Type"] == "correlation"
    ][[
        "Scenario",
        "GlobalScalar",
        "Gap_pct",
        "RichTW_pct",
        "MiddleTW_pct",
        "PoorTW_pct"
    ]].copy()

    corr_table = corr_table.rename(columns={
        "Gap_pct": "Gap %Δ",
        "RichTW_pct": f"{richName} TW %Δ",
        "MiddleTW_pct": f"{medName} TW %Δ",
        "PoorTW_pct": f"{poorName} TW %Δ"
    })

    _make_table_pretty(
        corr_table,
        "Correlation Sensitivity",
        graph_dir
    )

    # ==========================================================
    # BUSINESS WEALTH
    # ==========================================================

    business_table = summary[
        summary["Type"] == "business_wealth"
    ][[
        "Scenario",
        "smallBlend",
        "largeBlend",
        "alphaBusRaw",
        "busEpsScalar",
        "Gap_pct",
        "RichTW_pct",
        "MiddleTW_pct",
        "PoorTW_pct"
    ]].copy()

    business_table = business_table.rename(columns={
        "Gap_pct": "Gap %Δ",
        "RichTW_pct": f"{richName} TW %Δ",
        "MiddleTW_pct": f"{medName} TW %Δ",
        "PoorTW_pct": f"{poorName} TW %Δ"
    })

    _make_table_pretty(
        business_table,
        "Business Wealth Sensitivity",
        graph_dir
    )
    # ==========================================================
    # DF_T / TAIL RISK
    # ==========================================================

    df_table = summary[
        summary["Type"] == "df_t"
    ][[
        "Scenario",
        "df_t",
        "Gap_pct",
        "RichTW_pct",
        "MiddleTW_pct",
        "PoorTW_pct"
    ]].copy()

    df_table = df_table.sort_values("df_t")

    df_table = df_table.rename(columns={
        "df_t": "Degrees of Freedom",
        "Gap_pct": "Gap %Δ",
        "RichTW_pct": f"{richName} TW %Δ",
        "MiddleTW_pct": f"{medName} TW %Δ",
        "PoorTW_pct": f"{poorName} TW %Δ"
    })

    _make_table_pretty(
        df_table,
        "Tail Risk Sensitivity (t-distribution)",
        graph_dir
    )
    returns_table = returns_table.sort_values("Return Scalar")
    vol_table = vol_table.sort_values("Vol Scalar")
    corr_table = corr_table.sort_values("GlobalScalar")
    df_table = df_table.sort_values("Degrees of Freedom")
    return {
        "returns": returns_table,
        "volatility": vol_table,
        "correlation": corr_table,
        "business_wealth": business_table,
        "df_t": df_table
    }

def run_comparable_result_analysis(comparable_results):

    if isinstance(comparable_results, dict) and "comparable_results" in comparable_results:
        actual_results = comparable_results["comparable_results"]
    else:
        actual_results = comparable_results

    comparable_df = flatten_results(actual_results, drop_raw=True)

    print("\n=== AVAILABLE LABELS IN DATASET ===")
    print("Categories:", comparable_df['Category'].unique())
    print("Level_1 Labels:", comparable_df['Level_1'].unique())
    print("===================================\n")

    tables = make_sensitivity_tables(comparable_df)

    return tables
# def run_sensitivity_metric_analysis(metric)
def run_comparable_result_analysis2(comparable_results):
  if isinstance(comparable_results, dict) and "comparable_results" in comparable_results:
        actual_results = comparable_results["comparable_results"]
  else:
      actual_results = comparable_results
  comparable_df = flatten_results(actual_results, drop_raw=True)

  print("\n=== AVAILABLE LABELS IN DATASET ===")
  print("Categories:", comparable_df['Category'].unique())
  print("Level_1 Labels:", comparable_df['Level_1'].unique())
  print("===================================\n")
  # stuff to analyse:
  # 1. Wealth Gap Sensitivity
  # 2. Asset Contributions to said Gap Sensitivty
  # 3. Validation Sensitivty (CRPS, etc)
  # rows = []
  # for scenario_name, scenario_df in df.groupby("Scenario"):
  #   gap_rows = scenario_df[scenario_df['Category'] == 'gap_results']
  #   mean_values = gap_rows[gap_rows['Metric'] == 'mean']
  #   mean_value = mean_values[mean_values['Level_1'] == '80-100 vs 0-20'].item()


    # rows.append(scenario_name, mean_value)
  
  def runComparision(category, item, metric, item_name_reporting, flat_df):
    comparisionMask = ((flat_df['Category'] == category) & (flat_df['Level_1'] == item) & (flat_df['Metric'] == metric))
    comparisionRow = flat_df[comparisionMask].copy()
    if comparisionRow.empty:
      print(f"Error: no rows matching {category}, {item}, {metric}")
      return pd.DataFrame()
    
    baseline = comparisionRow['Scenario'] == 'baseline'
    if not baseline.any():
      print(f"Notice_me: Baseline scenario row missing. :(  ({category}, {item}, {metric}))")
      return pd.DataFrame()
    baseline_val = comparisionRow.loc[baseline, 'Value'].values[0]
    reportDF = comparisionRow[['Scenario', 'Type', 'muScalar', 'volScalar', 'Value']].copy()
    reportDF = reportDF.rename(columns={'Value': item_name_reporting})
    reportDF['Δ'] = reportDF[item_name_reporting] - baseline_val
    reportDF['%Δ'] = (reportDF[item_name_reporting] - baseline_val) / (0.5 * (abs(reportDF[item_name_reporting]) + abs(baseline_val)) + 1e-12) 

    pct_delta_input = np.where(
       reportDF['Type'] == 'returns', reportDF['muScalar'] - 1.0,
       np.where(reportDF['Type'] == 'volatility', reportDF['volScalar'] - 1.0, 0)
    )
    
    valid = reportDF['Type'].isin(['returns', 'volatility'])
    # reportDF['Elasticity'] = np.where(
    #    pct_delta_input != 0.0,
    #    reportDF['%Δ'] / pct_delta_input,
    #    np.nan # baseline row = NaN bc: obvs.
    # )
    reportDF['Elasticity'] = np.where(
      valid & (pct_delta_input != 0),
      reportDF['%Δ'] / pct_delta_input,
      np.nan
      )
    reportDF['is_baseline'] = reportDF['Scenario'] == 'baseline'
    reportDF = reportDF.sort_values(by="is_baseline", ascending=False).drop(columns='is_baseline')
    if 'graph_dir' in globals():
      _make_table_pretty(reportDF, f"{category}, {item} sensitivty test", graph_dir)
    return reportDF.reset_index(drop=True)
  
  
  # gap_sensitivty = runComparision('gap_results', '80-100 vs 0-20', 'mean', 'Mean Gap', comparable_df)
  # print(gap_sensitivty)
  # rich_terminal_wealth_sensitivity = runComparision('mean_household_results', '80-100', 'terminal', 'Mean Terminal Wealth', comparable_df)
  # print(rich_terminal_wealth_sensitivity)
  # poor_terminal_wealth_sensitivity = runComparision('mean_household_results', '0-20', 'terminal', 'Mean Terminal Wealth', comparable_df)
  # print(poor_terminal_wealth_sensitivity)
    #  gap_mean = scenario_df["gap_results"]
     

  
  #  def flatten_results(resultsDict):
import traceback
#   !pip install stackprinter
import stackprinter
import time as tm
import copy   

def runSensitivityTests(inputParameters, scenarios, metric_config, V_num, testOneChunk=False, selection=None, sensitivityResults=None, nPaths=None, chunkSize=None, master_seed=None):

  

       
       
  if sensitivityResults is None:
      sensitivityResults = {}
  
  stage = "sensitivity_run"
  failed_count = 0 
  try:
      print("=== SETUP ===")
      cfg = setup()
      if inputParameters is None:
        inputParameters = cfg["inputParameters"]
      if metric_config is None:
         metric_config = cfg["metric_config"]
      if scenarios is None:
         scenarios = cfg["scenarios"]
        


  except Exception:
      print("FAILED IN SETUP")
      traceback.print_exc()
      stackprinter.show(style='lightbg')
      raise
  cfg = copy.deepcopy(cfg)
  if nPaths != None:
    cfg["inputParameters"]["Chunks"]["totalPaths"] = nPaths
  if chunkSize != None:
    cfg["inputParameters"]["Chunks"]["chunkSize"] = chunkSize
  # Step 2: getting data
  try:
        print("=== COEFF FITTING ===")
        # coeffsDict, returnsDict = getCoeffs(assets, assetsCompleted, assetsYahoo, assetWeights, households, time, corrAbleClasses, {}, inputParameters)
        coeffsDict, returnsDict, fullCorr, allTickersOrdered = getCoeffs(cfg["assets"], cfg["assetsCompleted"], cfg["assetsYahoo"], cfg["assetWeights"], cfg["households"], cfg["time"], cfg["corrAbleClasses"], {}, inputParameters)
        print(f"RAM: (getCoeffs) {psutil.Process().memory_info().rss / 1024**3:.2f} GB")
        # returns_array = np.array(list(returnsDict.values()))
        # excessDays = np.sum(np.abs(returns_array) > 0.5)
        # total_days = len(returnsDict)
        # max_allowed_bad_days = total_days * 0.05  # 5% threshold

        # # Asserts that the count of excessDays is within limits
        # assert excessDays <= max_allowed_bad_days, (
        #     f"returnsDict has total days exceeding 50%: {excessDays} out of {total_days}"
        # )
        explode_test(3, returnsDict, "get_coeffs runSenstest")
        # assert np.any(np.abs(returnsDict) < 0.6), f"returnsDict has total days exceeding 50%: {np.sum(returnsDict.abs()) > 0.5)} out of {len(r)}"
  except Exception:
        print("FAILED IN GETCOEFFS")
        traceback.print_exc()
        stackprinter.show(style='lightbg')
        raise

  if selection == None:
     selection = "all"
  
  allTypes = [item.get("type", None) for item in scenarios]

  filtered = [
     item for item in scenarios if (selection == "all" and item.get("type") in allTypes) 
     or (item.get("name") in selection)
  ]
  for scenario in filtered:
    scenarioType = scenario.get("type").lower()
    scenarioName = scenario.get("name")
    # base_coeffs = copy.deepcopy(coeffsDict)
    inputParametersInitial = copy.deepcopy(cfg["inputParameters"])
    scenario_coeffs = copy.deepcopy(coeffsDict)
    print(f"\n>>> APPLYING SCENARIO: {scenarioName} <<<")
    
    if scenarioType == "correlation":
       
      inputParametersInitial["Correlation Modifier"]["Global Scalar"] = scenario.get("Global Scalar")
      inputParametersInitial["Correlation Modifier"]["Mode"] = scenario.get("Mode")
      inputParametersInitial["Correlation Modifier"]["assetClassScalars"] = scenario.get("assetClassScalars", inputParametersInitial["Correlation Modifier"].get("assetClassScalars"))
    elif scenarioType == "df_t":
      inputParametersInitial["Overall"]["df_t"] = scenario.get("df_t")
    elif scenarioType == 'business_wealth':
      busParams = inputParametersInitial["Busniess Equity"]
      for key, value in scenario.items():
         if key in busParams:
            inputParametersInitial["Busniess Equity"][key] = value
        #  inputParametersInitial["Busniess Equity"][heading] = scenario.get(heading, inputParametersInitial["Busniess Equity"][heading])

    if scenarioType in ["correlation", "business_wealth"]:
        # recalculate getCoeffs because underlying data/matrices changed
        scenario_coeffs, _, scenario_fullCorr, scenario_tickers = getCoeffs(
            cfg["assets"], cfg["assetsCompleted"], cfg["assetsYahoo"], 
            cfg["assetWeights"], cfg["households"], cfg["time"], 
            cfg["corrAbleClasses"], {}, inputParametersInitial
        )
    else:
        # Re-use baseline matrices for speed
        scenario_coeffs = scenario_coeffs #copy.deepcopy(coeffsDict)
        scenario_fullCorr = fullCorr
        scenario_tickers = allTickersOrdered

    if scenarioType == "returns" or scenarioType == "volatility":
       
      muScalar = scenario.get("muScalar", 1.0)
      volScalar = scenario.get("volScalar", 1.0)
      scenario_coeffs = applyReturnShock(coeffsDict=coeffsDict, muScalar=muScalar, volScalar=volScalar)
    print(f"RAM: (applying scenario) {psutil.Process().memory_info().rss / 1024**3:.2f} GB")
    # Step 2: running baseline
    try:
      t0 = tm.perf_counter()
      print("=== CHUNK SIMULATION ===")
      # if debugLocal: V_num = "debug"
      aggres = runChunks(inputParametersInitial, scenario_coeffs, scenario_fullCorr, scenario_tickers, cfg["assetWeights"], cfg["assets"], cfg["assetsCompleted"], cfg["assetsYahoo"], cfg["corrAbleClasses"], cfg["households"], cfg["time"], returnsDict, cfg["folder"], V_num=f"{V_num}_{scenarioName}", testOneChunk=testOneChunk, master_seed=master_seed)
      print(f"RAM: (running chunks) {psutil.Process().memory_info().rss / 1024**3:.2f} GB")
      # aggres = runChunks(inputParametersInitial, scenario_coeffs, assetWeights, assets, assetsCompleted, assetsYahoo, corrAbleClasses, households, time, 
      #                    returnsDict, folder, V_num=f"{V_num}_{scenarioName}", testOneChunk=testOneChunk)
      # aggres
    except Exception:
      print(f"FAILED IN RUN CHUNKS")
      traceback.print_exc()
      stackprinter.show(style='lightbg')
      raise


    try:
        print("=== ASSET AGGREGATION ===")

        assetResults = aggregate_to_asset_paths(
            nTotalPaths=inputParametersInitial["Chunks"]["totalPaths"],
            V_num=f"{V_num}_{scenarioName}",
        )
        print(f"RAM: (asset aggregation) {psutil.Process().memory_info().rss / 1024**3:.2f} GB")
    except Exception:
        print("FAILED IN ASSET AGGREGATION")
        traceback.print_exc()
        stackprinter.show(style='lightbg')
        raise


    try:
        print("=== PORTFOLIO AGGREGATION ===")

        aggRes = portfolioAggregation(
            assetWeights=cfg["assetWeights"],
            fullSavedAssetRes=assetResults,
            households=cfg["households"],
            assetsCompleted=cfg["assetsCompleted"]
        )
        print(f"RAM: (port agg) {psutil.Process().memory_info().rss / 1024**3:.2f} GB")
    except Exception:
        print("FAILED IN PORTFOLIO AGGREGATION")
        traceback.print_exc()
        stackprinter.show(style='lightbg')
        raise

        # runGraphs(aggRes, assetResults, time, households, graph_dir, metric_results, tablesNeeded=True, plots_to_generate=None):
    try:
        cache_file = Path(data_dir) / f"Aggregated_State_{scenarioName}_{V_num}.pkl"
        if cache_file.exists():
            print(f"Loading cached analysis: {cache_file}")

            with open(cache_file, "rb") as f:
                cached = pickle.load(f)

            aggRes = cached["aggRes"]
            assetResults = cached["assetResults"]
            metric_results = cached["metric_results"]
            # time = cached["time"]
            households = cached["households"]
            # sensitivityResults = cached["sensitivityResults"]
            cached_sr = cached.get("sensitivityResults", {})
            if scenarioName in cached_sr:
                sensitivityResults[scenarioName] = cached_sr[scenarioName]
            elif scenarioName in cached.get("comparable_results_new", {}):
                sensitivityResults[scenarioName] = cached["comparable_results_new"][scenarioName]
        else:
            print("=== ANALYSIS ===")

            metric_results = get_metric_analysis(
              chunk_folder=cfg["chunkFolder"],
              coeffs_dict=scenario_coeffs,
              assets_completed=cfg["assetsCompleted"],
              asset_weights=cfg["assetWeights"],
              households=cfg["households"],
              time_hist=cfg["time"],
              V_num=f"{V_num}_{scenarioName}",
              percentile_bands=inputParametersInitial["percentile_bands"],
              aggRes = aggRes,  # idk
              asset_level_res = assetResults

            )
            print(f"RAM: (metric anaylsis) {psutil.Process().memory_info().rss / 1024**3:.2f} GB")

            # print(f"WOOOOO results: {metric_results['house_cum_results']['house_cum_df']}")
            sensitivityResults = get_comparable_results(metric_results, scenarioName, inputParametersInitial, metric_config, scenario_coeffs, sensitivityResults, scenario)
            # if testOneChunk:

            print(f"RAM: (sensitivity res) {psutil.Process().memory_info().rss / 1024**3:.2f} GB")
            
            print(f"[{scenarioName}] Chunk analysis complete. Saving to cache...")
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'aggRes': aggRes,
                    'assetResults': assetResults,
                    'metric_results': metric_results,
                    # "comparable_results_new": comparable_results_new,
                    # 'time': time,
                    'households': cfg["households"],
                    'sensitivityResults': sensitivityResults 
                }, f)
        #    continue
    except Exception:
        print("FAILED IN ANALYSIS")
        traceback.print_exc()
        stackprinter.show(style='lightbg')
        raise
  try:
      print("=== GRAPHING ===")

      runGraphs(
          aggRes=aggRes,
          assetResults=assetResults,
          time=cfg["time"],
          households=cfg["households"],
          graph_dir=graph_dir,
          metric_results=metric_results,
          tablesNeeded=True
      )
      print(f"RAM: (graphing) {psutil.Process().memory_info().rss / 1024**3:.2f} GB")
  except Exception:
      print("FAILED IN GRAPHING")
      traceback.print_exc()
      stackprinter.show(style='lightbg')
      raise

  _save_item(sensitivityResults, path=None, base_path=data_dir, add_to_base=f"comparable_results_{V_num}")
  return {
    "comparable_results": sensitivityResults
  }# runSensitivityTests(inputParameters, scenarios, "Sensitivity")
# print(fullSavedAssetRes['sigmaAssetClassPath'].keys())

#=====================================
# main(inputParameters, 8)
#=====================================

# currentRun = 126
# baseline_output = main(V_num=f"baseline_debug{currentRun}", inputParameters=None, testOneChunk=True)
# baseline_dict = baseline_output["comparable_results"] 
# selection = ['HigherReturns10', "globalHigher10", "SmallCapHeavy"]
# comparable_results = runSensitivityTests(inputParameters=None, scenarios=None, metric_config=None, V_num=f"sensitivityDebug{currentRun}", testOneChunk=True, selection=None, sensitivityResults=baseline_dict)
# try:
#   run_comparable_result_analysis(comparable_results)
# except Exception:
#         print("FAILED IN sensitivty analysis")
#         traceback.print_exc()
#         stackprinter.show(style='lightbg')
#         raise

def runAnalysisGraphingPipelineOnly(inputParameters, scenarios, metric_config, V_num, testOneChunk=False, selection=None, sensitivityResults=None):
   
    
    # 1. Run Setup and Coeff fitting to get the required baseline metadata structures
    print("=== SETUP & COEFF FITTING ===")
    (
        assetsCompleted, assetsYahoo, assets, assetWeights, 
        households, time, folder, chunkFolder, corrAbleClasses
    ) = setup()
    
    coeffsDict, returnsDict = getCoeffs(assets, assetsCompleted, assetsYahoo, assetWeights, households, time, corrAbleClasses, {}, inputParameters)
    explode_test(3, returnsDict, "main() runChunks")

    if selection == None:
        selection = "all"
  
    allTypes = [item.get("type", None) for item in scenarios]
    filtered = [item for item in scenarios if (selection == "all" and item.get("type") in allTypes) or (item.get("type") == selection)]
  
    for scenario in filtered:
        scenarioType = scenario.get("type").lower()
        scenarioName = scenario.get("name")
        scenario_V_num = f"{V_num}_{scenarioName}"
    
        print(f"\n>>> PROCESSING METRICS FOR SCENARIO: {scenarioName} (Targeting: {scenario_V_num}) <<<")
        print(f"\n>>> PROCESSING METRICS FOR SCENARIO: {scenarioName} <<<")
        
        # Recreate parameter mutations so metrics align
        inputParametersInitial = copy.deepcopy(inputParameters)
        if scenarioType == "returns" or scenarioType == "volatility":
            muScalar = scenario.get("muScalar", 1.0)
            volScalar = scenario.get("volScalar", 1.0)
            scenario_coeffs = applyReturnShock(coeffsDict=coeffsDict, muScalar=muScalar, volScalar=volScalar)
        elif scenarioType == "correlation":
            scenario_coeffs = copy.deepcopy(coeffsDict)
            inputParametersInitial["Correlation Modifier"]["Global Scalar"] = scenario.get("Global Scalar")
            inputParametersInitial["Correlation Modifier"]["Mode"] = scenario.get("Mode")
        else:
            scenario_coeffs = copy.deepcopy(coeffsDict)

        
        try:
            print("=== ASSET AGGREGATION ===")
            assetResults = aggregate_to_asset_paths(
                nTotalPaths=inputParametersInitial["Chunks"]["totalPaths"],
                V_num=scenario_V_num
            )

            print("=== PORTFOLIO AGGREGATION ===")
            aggRes = portfolioAggregation(
                assetWeights=assetWeights,
                fullSavedAssetRes=assetResults,
                households=households,
                assetsCompleted=assetsCompleted
            )

            print("=== ANALYSIS ===")
            metric_results = get_metric_analysis(
                chunk_folder=chunkFolder,
                coeffs_dict=scenario_coeffs, 
                assets_completed=assetsCompleted,
                asset_weights=assetWeights,
                households=households,
                time_hist=time,
                V_num=scenario_V_num,
                percentile_bands=inputParametersInitial["percentile_bands"],
                aggRes=aggRes,  
                asset_level_res=assetResults
            )
            cache_file = Path(data_dir) / f"Aggregated_State_{scenarioName}_V{V_num}.pkl"
            if cache_file.exists():
                print(f"Loading cached analysis: {cache_file}")

                with open(cache_file, "rb") as f:
                    cached = pickle.load(f)

                aggRes = cached["aggRes"]
                assetResults = cached["assetResults"]
                metric_results = cached["metric_results"]
                # time = cached["time"]
                # households = cached["households"]
            else:
                print(f"[{scenarioName}] Chunk analysis complete. Saving to cache...")
                with open(cache_file, 'wb') as f:
                    pickle.dump({
                        'aggRes': aggRes,
                        'assetResults': assetResults,
                        'metric_results': metric_results,
                        'time': time,
                        'households': households
                    }, f)
            sensitivityResults = get_comparable_results(
                metric_results, scenarioName, inputParametersInitial, 
                metric_config, scenario_coeffs, sensitivityResults, scenario
            )

            print("=== GRAPHING ===")
            runGraphs(
                aggRes=aggRes,
                assetResults=assetResults,
                time=time,
                households=households,
                graph_dir=graph_dir,
                metric_results=metric_results,
                tablesNeeded=True
            )

        except Exception as e:
            print(f"Failed processing scenario {scenarioName}")
            if hardCrash:
                raise e
            else:
              log_pipeline_failure(
                  e,
                  stage="run_analysis",
                  V_num=V_num,
                  # fname=fname,
                  # chunkIndex=chunkIndex,
                  hardCrash=hardCrash,
                  message = f"Failed processing scenario {scenarioName}"
              )
              continue

    return {"comparable_results": sensitivityResults}

# Execute the analysis loop directly
# analysis_output = runAnalysisPipelineOnly(inputParameters, scenarios, metric_config, "sensitivityDebug2", testOneChunk=True)
# run_comparable_result_analysis(analysis_output)