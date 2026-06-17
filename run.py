import unseperated_main as m
import traceback
import stackprinter

def main2():
    currentRun = 27

    baseline_output = m.main(
        V_num=f"baseline_debug{currentRun}",
        inputParameters=None,
        testOneChunk=False
    )

    baseline_dict = baseline_output["comparable_results"]

    # selection = ['HigherReturns10', "globalHigher10", "SmallCapHeavy"]

    comparable_results = m.runSensitivityTests(
        inputParameters=None,
        scenarios=None,
        metric_config=None,
        V_num=f"sensitivityDebug{currentRun}",
        testOneChunk=False,
        selection=None,
        sensitivityResults=baseline_dict,
        nPaths=5000
    )

    try:
        m.run_comparable_result_analysis(comparable_results)
    except Exception:
        print("FAILED IN sensitivity analysis")
        traceback.print_exc()
        stackprinter.show(style='lightbg')
        raise

if __name__ == "__main__":
    main2()