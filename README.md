# Reading the Fed: A Text-Based Analysis of FOMC Statements and Market Reactions

This project investigates whether the tone of Federal Open Market Committee statements is associated with short-run movements in financial markets. The analysis uses Python to scrape FOMC statements, clean and process text, construct hawkisg/dovish tone scores, merge the tone data with market data, run simple regressions, and generate figures for a Quarto blog post.

## Question

Do more hawkish FOMC statements coincide with changes in:
- the US 2-year Treasury yield
- S&P 500 returns
- the US dollar index?

## Data

The project uses:
- FOMC statement text scraped from the Federal Reserve website
- daily market data containing the US 2-year Treasury yield, S&P 500, and US dollar index

## Project Structure

- `scripts/`: Python scripts used to scrape, clean, merge, analyse, and visualise the data
- `data/raw/`: raw input data
- `data/processed/`: cleaned and merged datasets
- `output/figures/`: static figures
- `output/interactive_figures/`: interactive Plotly figures
- `output/tables/`: summary statistics, regression results, and robustness check
- `posts/fed-text-markets/`: Quarto blog post


## How to Reproduce

### Install the required packages:

```bash
pip3 install -r requirements.txt
```

### Run the scripts from the project root in this order:
```bash
python3 scripts/01_scrape_fed_statements.py
python3 scripts/02_clean_fed_statements.py
python3 scripts/03_build_tone_scores.py
python3 scripts/03b_compare_tone_dictionaries.py
python3 scripts/04_prepare_market_data.py
python3 scripts/05_merge_event_dataset.py
python3 scripts/06_run_analysis.py
python3 scripts/07_make_figures.py
python3 scripts/08_make_interactive_figures.py
```

### Render the Quarto website
```bash
quarto render
```

### Main Outputs
```bash
- data/processed/analysis_dataset.csv
- output/tables/summary_stats.csv
- output/tables/regression_results.csv
- output/tables/regression_summary_blog.csv
- output/tables/dictionary_comparison.csv
- output/figures/
- output/interactive_figures/
```

## Method Summary

**The tone score is calculated as:**
*Tone Score = Hawkish Count - Dovish Count*

**The normalised tone score is calculated as:**
*Normalised Tone Score = Tone Score/Word Count*

**The market reaction variables are:**
- us2yield_change: daily change in the US2-year Treasury yield
- sp500_return: daily percentage return of the S&P 500
- usd_index_change: daily percentage change in the US dollar index

## Limitations

The tone score is dictionary-based and it does not capture context, negation, or the broader policy environment to a full extent. The regressions are associations, not causal estimates.





# Reading the Fed: A Text-Based Analysis of FOMC Statements and Market Reactions
 
This project investigates whether the tone of Federal Open Market Committee statements is associated with short-run movements in financial markets. The analysis uses Python to scrape FOMC statements, clean and process text, construct hawkish/dovish tone scores, merge the tone data with market data, run simple regressions, and generate figures for a Quarto blog post.
 
## Question
 
Do more hawkish FOMC statements coincide with changes in:
- the US 2-year Treasury yield
- S&P 500 returns
- the trade-weighted US dollar index?
## Data
 
The project uses:
- FOMC statement text scraped from the Federal Reserve website (https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm)
- daily market data from FRED, containing:
  - `DGS2`: US 2-year Treasury constant maturity yield
  - `SP500`: S&P 500 closing price
  - `DTWEXBGS`: Trade-Weighted U.S. Dollar Index, Broad, Goods and Services
## Project Structure
 
- `scripts/`: Python scripts used to scrape, clean, merge, analyse, and visualise the data
- `data/raw/`: raw input data
- `data/processed/`: cleaned and merged datasets
- `output/figures/`: static figures
- `output/interactive_figures/`: interactive Plotly figures
- `output/tables/`: summary statistics, regression results, and robustness checks
- `posts/fed-text-markets/`: Quarto blog post
## How to Reproduce
 
### Install the required packages:
 
```bash
pip3 install -r requirements.txt
```
 
### Run the scripts from the project root in this order:
```bash
python3 scripts/01_scrape_fed_statements.py
python3 scripts/02_clean_text.py
python3 scripts/03_build_tone_scores.py
python3 scripts/03b_compare_tone_dictionaries.py
python3 scripts/04_prepare_market_data.py
python3 scripts/05_merge_event_dataset.py
python3 scripts/06_run_analysis.py
python3 scripts/07_make_figures.py
python3 scripts/08_make_interactive_figures.py
```
 
### Render the Quarto website
```bash
quarto render
```
 
### Main Outputs
- `data/processed/analysis_dataset.csv`
- `output/tables/summary_stats.csv`
- `output/tables/regression_results.csv`
- `output/tables/regression_summary_table.csv`
- `output/tables/dictionary_comparison.csv`
- `output/figures/`
- `output/interactive_figures/`
## Method Summary
 
**The tone score is calculated as:**
 
*Tone Score = Hawkish Count − Dovish Count*
 
**The normalised tone score is calculated as:**
 
*Normalised Tone Score = Tone Score / Word Count*
 
**The market reaction variables are:**
- `us2yield_change`: daily change in the US 2-year Treasury yield
- `sp500_return`: daily percentage return of the S&P 500
- `usd_index_change`: daily percentage change in the trade-weighted US dollar index
Regressions are estimated by OLS with heteroskedasticity-robust (HC3) standard errors.
 
## Notes on the Sample
 
The scraper picks up all monetary policy press releases from the Federal Reserve archive. The 22 August 2025 release was a non-standard document — the FOMC's quinquennial update to its *Statement on Longer-Run Goals and Monetary Policy Strategy* — and is filtered out at the scraping stage so it is not treated as a regular FOMC statement.
 
## Limitations
 
The tone score is dictionary-based and does not capture context, negation, or the broader policy environment. The regressions are associations, not causal estimates. The sample is small (42 statements) and same-day market data may include information from sources other than the statement itself (e.g. the press conference, Summary of Economic Projections, or unrelated macro news on the same day). See the blog post for a fuller discussion of limitations and robustness checks.