# Wealth-Divergence-Modelling
Stochastic model simulating proxy portfolios for Irish income cohorts to evaluate wealth divergence

## Overview
This repository contains the quantitative model and codebase for simulating wealth divergence across different income cohorts in Ireland over a 24-year horizon. By isolating empirically observed asset allocation differences and holding initial wealth and savings rates constant, the model evaluates the mechanistic contribution of asset management to wealth inequality.

**Core Finding** Simulations of representative portfolios demonstrate that differences in asset allocaiton alone generate a 37% divergence in expected long-run cumulative returns between high-income and low-income households.

## Data Sources
Asset allocation weights and historical proxy data are derived from:
* **Central Statistics Office (CSO):** Household Finance and Consumption Survey (HFC2057), Residential Property Price Index (RRPI)
*  **Yahoo Finance:** Daily historical price data for liquid proxy assets (Equities, Bonds)
*  **Central Bank of Ireland:** ‘Retail Investor Participation in Ireland Consumer Research and Analysis’, and Securities Statistics series for approximate composition of CSO asset categories.
  
## Methodology
- **Asset Classes**: Equities, Long-term Bonds, Short-term bonds, Property, Business Wealth, Deposits
- **Volatility**: Modelled using Garch(1,2) for liquid assets, and constant variance marginals for property and deposits, which only have monthly data insufficient for GARCH.
- **Dependence Structure**: Inter-asset correlations are mapped using a derived historical covariance matrix and applied via a Student-t copula and Cholesky decomposition to capture fat-tailed risk and empirical correlation structures.
- **Validation Testing**: Model accuracy is verified via Monte Carlo Convergence tracking, Continuous Ranked Probability Score (CRPS) calculation, and rolling-window coverage testing against historical data
- **Sensitivity Analysis**: 24 sensitivity isolated parameter sensitivty tests using Common Random Numbers for cross-comparision were used to measure impacts on core findings.

 ## Code Formatting
 - Model architecture uses modular functions, handling data setup, stochastic path generation (asset, portfolio and cohort levels), and output generation 
 - Functions are stored within the same file for common access to global debugging flags

## Execution 
 - Requirements must be installed from requirements.txt
 - main.py automatically runs the model, verifying if saved aggregations already exist and downloading them locally, running graphing and table generation and saving to a local folder.
 - To re-compute model operation and path generation from scratch, open main.py, then modify version string V_num (i.e, set to 'test_run'). You can optionally modify the desired number of Monte Carlo iterations by varying nPaths (default is 5,000). Note that full simulation is time and resource intensive.
 - The code will download 10+ GB of aggregated data neccasary to locally generate outputs and graphs for verification. It will do so in the location assigned by your terminal, so it may be advisble to change location, for instance by running: cd C:\Users\[user_name]\[file path]
 - All graphs will be displayed for the baseline results. 

### Direct operation code:
'''bash
# Clone the repository
git clone https://github.com/neoghan30-byte/wealth-divergence-modelling.git
cd wealth-divergence-modelling
pip install -r requirements.txt
# Execute the primary simulation script
python main.py

