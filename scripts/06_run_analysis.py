import pandas as pd
import statsmodels.api as sm
from pathlib import Path


def significance_stars(p_value):
    if p_value < 0.01:
        return "***"
    elif p_value < 0.05:
        return "**"
    elif p_value < 0.10:
        return "*"
    else:
        return ""

def run_model(df, y_var, x_vars, cov_type="HC3"):
    """
    Run an OLS regression of y_var on x_vars (plus a constant).
    Standard errors are heteroskedasticity-robust (HC3) by default,
    because financial returns are typically heteroskedastic.
    """
    model_df = df[[y_var] + x_vars].dropna()

    X = model_df[x_vars]
    X = sm.add_constant(X)
    y = model_df[y_var]

    model = sm.OLS(y, X).fit(cov_type=cov_type)
    return model, model_df

def main():
    input_path = Path("data/processed/analysis_dataset.csv")
    output_dir = Path("output/tables")
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)

    # Add a linear time trend (in years from the first FOMC date in the sample)
    # Used as a control variable in the robustness check below.
    df["time_trend"] = (df["date"] - df["date"].min()).dt.days / 365.25

    print("Rows loaded:", len(df))

    # =========================================================
    # Summary statistics
    # =========================================================
    summary_vars = [
        "tone_score", "tone_score_norm",
        "tone_score_change", "tone_score_norm_change",
        "us2yield_change", "sp500_return", "usd_index_change"
    ]

    summary_stats = df[summary_vars].describe().round(4)
    summary_stats.to_csv(output_dir / "summary_stats.csv", float_format="%.4f")

    summary_table = summary_stats.T.reset_index()
    summary_table = summary_table.rename(columns={
        "index": "variable",
        "count": "n",
        "std": "standard_deviation",
        "min": "minimum",
        "25%": "q1",
        "50%": "median",
        "75%": "q3",
        "max": "maximum"
    })

    summary_table = summary_table[
        ["variable", "n", "mean", "standard_deviation",
         "minimum", "q1", "median", "q3", "maximum"]
    ]

    summary_table["n"] = summary_table["n"].astype(int)
    summary_table.to_csv(
        output_dir / "summary_stats_table.csv",
        index=False, float_format="%.4f"
    )

    print("Saved summary statistics.")
    print(summary_table.to_string(index=False))

    # =========================================================
    # Main regressions (HC3 robust standard errors)
    # =========================================================
    regression_results = []

    models = {
        "baseline_us2y": ("us2yield_change", ["tone_score_norm"]),
        "baseline_sp500": ("sp500_return", ["tone_score_norm"]),
        "baseline_usd": ("usd_index_change", ["tone_score_norm"]),
        "change_us2y": ("us2yield_change", ["tone_score_norm_change"]),
        "change_sp500": ("sp500_return", ["tone_score_norm_change"]),
        "change_usd": ("usd_index_change", ["tone_score_norm_change"])
    }

    for model_name, (y_var, x_vars) in models.items():
        model, model_df = run_model(df, y_var, x_vars)

        print(f"\nRegression results for {model_name} (HC3 robust SE)")
        print(model.summary())

        for var in model.params.index:
            regression_results.append({
                "model_name": model_name,
                "dependent_variable": y_var,
                "variable": var,
                "coefficient": model.params[var],
                "std_error": model.bse[var],
                "t_stat": model.tvalues[var],
                "p_value": model.pvalues[var],
                "r_squared": model.rsquared,
                "n_obs": int(model.nobs)
            })

    results_df = pd.DataFrame(regression_results)

    results_df = results_df.round({
        "coefficient": 4,
        "std_error": 4,
        "t_stat": 4,
        "p_value": 4,
        "r_squared": 4,
        "n_obs": 0
    })

    results_df.to_csv(
        output_dir / "regression_results.csv",
        index=False, float_format="%.4f"
    )

    # Cleaner one-row-per-model table
    main_results = results_df[results_df["variable"] != "const"].copy()
    main_results["significance"] = main_results["p_value"].apply(significance_stars)
    main_results["coefficient_with_stars"] = (
        main_results["coefficient"].map(lambda x: f"{x:.4f}")
        + main_results["significance"]
    )

    regression_table = main_results[[
        "model_name", "dependent_variable", "variable",
        "coefficient_with_stars", "std_error", "t_stat",
        "p_value", "r_squared", "n_obs"
    ]]

    regression_table = regression_table.rename(columns={
        "model_name": "model",
        "dependent_variable": "dependent variable",
        "variable": "explanatory variable",
        "coefficient_with_stars": "coefficient",
        "std_error": "standard error",
        "t_stat": "t-statistic",
        "p_value": "p-value",
        "r_squared": "R-squared",
        "n_obs": "observations"
    })

    regression_table.to_csv(
        output_dir / "regression_summary_table.csv",
        index=False, float_format="%.4f"
    )

    print("\nClean regression summary table:")
    print(regression_table.to_string(index=False))

    # =========================================================
    # Robustness check: tone + time trend on the 2Y yield
    #
    # The headline result (Model 1) is a statistically significant
    # NEGATIVE coefficient on tone for the 2-year yield change.
    # Because the normalised tone score has trended over the sample
    # period (driven partly by statements becoming shorter from 2022
    # onwards), a natural concern is that the relationship is a
    # spurious correlation between two time-trending variables.
    # Adding a linear time trend lets us check whether the tone
    # coefficient survives.
    # =========================================================
    print("\n" + "=" * 60)
    print("ROBUSTNESS CHECK: tone + time trend -> 2Y yield change")
    print("=" * 60)

    rob_model, _ = run_model(
        df, "us2yield_change", ["tone_score_norm", "time_trend"]
    )
    print(rob_model.summary())

    robustness_rows = []
    for var in rob_model.params.index:
        robustness_rows.append({
            "model_name": "robustness_us2y_with_trend",
            "dependent_variable": "us2yield_change",
            "variable": var,
            "coefficient": round(rob_model.params[var], 4),
            "std_error": round(rob_model.bse[var], 4),
            "t_stat": round(rob_model.tvalues[var], 4),
            "p_value": round(rob_model.pvalues[var], 4),
            "r_squared": round(rob_model.rsquared, 4),
            "n_obs": int(rob_model.nobs)
        })

    robustness_df = pd.DataFrame(robustness_rows)
    robustness_df.to_csv(
        output_dir / "robustness_us2y_time_trend.csv",
        index=False, float_format="%.4f"
    )
    print("\nSaved robustness check (tone + time trend) for 2Y yield.")
    print(robustness_df.to_string(index=False))

    print(f"\nSaved regression results to "
          f"{(output_dir / 'regression_results.csv').resolve()}")

if __name__ == "__main__":
    main()