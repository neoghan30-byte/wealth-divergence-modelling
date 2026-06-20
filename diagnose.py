import unseperated_main as m

import pandas as pd
import numpy as np


def diagnose(coeffs_dict, assets_completed, time_hist):
    full_hist_index = pd.to_datetime(time_hist)
    print(f"full_hist_index: {len(full_hist_index)} entries, "
          f"{full_hist_index[0]} -> {full_hist_index[-1]}\n")

    for asset_class in assets_completed:
        for ticker in assets_completed[asset_class]:
            cd = coeffs_dict[asset_class][ticker]
            raw = cd.get("histRetMonthly", cd.get("histRet", cd.get("mu", None)))

            print(f"--- {asset_class} / {ticker} ---")
            if raw is None:
                print("  raw is None\n")
                continue

            print(f"  type(raw) = {type(raw)}")
            print(f"  has histRetMonthly key = {'histRetMonthly' in cd}, "
                  f"has histRet key = {'histRet' in cd} (value: "
                  f"{type(cd.get('histRet'))})")

            if isinstance(raw, (pd.Series, pd.DataFrame)):
                print(f"  len(raw) = {len(raw)}")
                print(f"  raw.index type = {type(raw.index)}")
                if isinstance(raw.index, pd.DatetimeIndex):
                    print(f"  raw.index range = {raw.index.min()} -> {raw.index.max()}")
                else:
                    print(f"  raw.index sample = {raw.index[:5].tolist()} "
                          f"(NOT a DatetimeIndex -- will be reassigned)")
            elif isinstance(raw, np.ndarray):
                print(f"  len(raw) = {len(raw)} (ndarray, no index at all)")
            print()

def run_diagnose():
    cfg = m.setup()
    inputParameters = cfg["inputParameters"]
    # if metric_config is None:
    #     metric_config = cfg["metric_config"]
    
    #   except Exception:
        #   print("FAILED IN SETUP")
        #   traceback.print_exc()
        #   stackprinter.show(style='lightbg')
        #   raise

    cfg = copy.deepcopy(cfg)
    # if nPaths != None:
    #     cfg["inputParameters"]["Chunks"]["totalPaths"] = nPaths
    # if chunkSize != None:
    #     cfg["inputParameters"]["Chunks"]["chunkSize"] = chunkSize
    # Step 2: getting data
    # try:
    print("=== COEFF FITTING ===")
    coeffsDict, returnsDict, fullCorr, allTickersOrdered = m.getCoeffs(cfg["assets"], cfg["assetsCompleted"], cfg["assetsYahoo"], cfg["assetWeights"], cfg["households"], cfg["time"], cfg["corrAbleClasses"], {}, inputParameters)
    # returns_array = np.array(list(returnsDict.values()))
    start = dt.datetime(2000, 1, 1)
    end = dt.datetime(2025, 1, 1)
    # time = []
    # for i in range((end - start).days):
    # # time.append(start + dt.timedelta(days=i))
    # extraTime = []
    # for i in range((end - (start - dt.timedelta(days=1))).days):
    # extraTime.append((start - dt.timedelta(days=1)) + dt.timedelta(days=i))

    time_dt = pd.bdate_range(start=start, end=end) # Business (252/yr)
    time = time_dt.to_pydatetime().tolist()
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




    diagnose(coeffsDict, assetsCompleted, time)
if __name__ == "diagnose.py" or True:
    run_diagnose()
    