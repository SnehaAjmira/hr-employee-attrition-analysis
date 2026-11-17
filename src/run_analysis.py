"""Run the SQL pipeline in DuckDB, fit an attrition risk model, export tables and figures.

Usage (from the repository root):
    python src/run_analysis.py
"""
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

import style

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "sql"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
SOURCE = "IBM HR Analytics Employee Attrition sample dataset (fictional employees)"

FEATURES = {
    "works_overtime": "Works overtime",
    "single": "Marital status: single",
    "travel_frequently": "Travels frequently",
    "no_stock_options": "No stock options",
    "job_level_1": "Job level 1 (entry)",
    "years_at_company": "Years at company (per year)",
    "income_k": "Monthly income (per 1,000)",
    "job_satisfaction": "Job satisfaction (per point, 1-4)",
    "environment_satisfaction": "Environment satisfaction (per point, 1-4)",
    "work_life_balance": "Work-life balance (per point, 1-4)",
    "distance_from_home": "Distance from home (per mile)",
    "age": "Age (per year)",
}


def run_sql(con):
    con.execute((SQL / "00_staging.sql").read_text())
    results = {}
    for path in sorted(SQL.glob("0[1-9]_*.sql")):
        df = con.execute(path.read_text()).df()
        df.to_csv(TABLES / f"{path.stem}.csv", index=False)
        results[path.stem] = df
    return results


def build_features(emp):
    X = pd.DataFrame({
        "works_overtime": emp.works_overtime.astype(int),
        "single": (emp.marital_status == "Single").astype(int),
        "travel_frequently": (emp.business_travel == "Travel Frequently").astype(int),
        "no_stock_options": (emp.stock_option_level == 0).astype(int),
        "job_level_1": (emp.job_level == 1).astype(int),
        "years_at_company": emp.years_at_company,
        "income_k": emp.monthly_income / 1000,
        "job_satisfaction": emp.job_satisfaction,
        "environment_satisfaction": emp.environment_satisfaction,
        "work_life_balance": emp.work_life_balance,
        "distance_from_home": emp.distance_from_home,
        "age": emp.age,
    })
    return X, emp.left_company.astype(int)


def fit_model(emp):
    """Logistic regression on a 70/30 stratified split; report odds ratios and holdout AUC."""
    X, y = build_features(emp)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)
    model = sm.Logit(y_train, sm.add_constant(X_train)).fit(disp=False)
    auc = roc_auc_score(y_test, model.predict(sm.add_constant(X_test)))

    ci = np.exp(model.conf_int())
    odds = pd.DataFrame({
        "feature": [FEATURES[f] for f in X.columns],
        "odds_ratio": np.exp(model.params[X.columns]).round(2).values,
        "ci_low": ci.loc[X.columns, 0].round(2).values,
        "ci_high": ci.loc[X.columns, 1].round(2).values,
        "p_value": model.pvalues[X.columns].round(4).values,
    }).sort_values("odds_ratio", ascending=False)
    summary = pd.DataFrame({
        "metric": ["Training rows", "Holdout rows", "Holdout ROC AUC", "Pseudo R-squared (McFadden)"],
        "value": [len(X_train), len(X_test), round(auc, 3), round(model.prsquared, 3)],
    })
    odds.to_csv(TABLES / "06_model_odds_ratios.csv", index=False)
    summary.to_csv(TABLES / "07_model_summary.csv", index=False)
    return odds, summary


def fig_drivers(df):
    picks = [
        ("Job role", "Sales Representative"), ("Overtime", "Yes"), ("Tenure", "1) 0-1 years"),
        ("Work-life balance (1 low to 4 high)", "1"), ("Income quartile", "Q1"), ("Job level", "1"),
        ("Marital status", "Single"), ("Business travel", "Travel Frequently"), ("Stock option level", "0"),
        ("Tenure", "5) 11+ years"), ("Job level", "4"), ("Job role", "Research Director"),
    ]
    labels = {
        "Sales Representative": "Role: Sales Representative", "Yes": "Works overtime",
        "1) 0-1 years": "Tenure: 0-1 years", "1": None, "Q1": "Income: lowest quartile",
        "Single": "Marital status: single", "Travel Frequently": "Travels frequently",
        "0": "No stock options", "5) 11+ years": "Tenure: 11+ years", "4": "Job level 4",
        "Research Director": "Role: Research Director",
    }
    rows = []
    for factor, level in picks:
        r = df[(df.factor == factor) & (df.level == level)].iloc[0]
        name = labels.get(level)
        if level == "1":
            name = "Work-life balance: 1 (low)" if factor.startswith("Work") else "Job level 1 (entry)"
        rows.append((name, r.attrition_pct))
    d = pd.DataFrame(rows, columns=["label", "pct"]).sort_values("pct")
    company = 16.1
    fig, ax = plt.subplots(figsize=(8, 5.4))
    colors = [style.SERIES[1] if p > company else style.SERIES[0] for p in d.pct]
    ax.barh(d.label, d.pct, color=colors, height=0.62)
    ax.axvline(company, color=style.TEXT_2, linewidth=1, linestyle="--")
    ax.text(company + 0.4, len(d) - 0.4, f"Company average {company}%", fontsize=8, color=style.TEXT_2)
    for y, p in enumerate(d.pct):
        ax.text(p + 0.5, y, f"{p:.1f}%", va="center", fontsize=8, color=style.TEXT)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_xlim(0, 45)
    ax.grid(axis="y", visible=False)
    ax.set_title("Attrition rate by employee group (orange: above company average)")
    style.finish(fig, FIGURES / "01_attrition_drivers.png", SOURCE)


def fig_overtime_level(df):
    p = df.pivot(index="job_level", columns="overtime", values="attrition_pct")
    x = np.arange(len(p))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(x - 0.19, p["No overtime"], width=0.36, color=style.NEUTRAL, label="No overtime")
    ax.bar(x + 0.19, p["Overtime"], width=0.36, color=style.SERIES[1], label="Overtime")
    for i, (a, b) in enumerate(zip(p["No overtime"], p["Overtime"])):
        ax.text(i - 0.19, a + 0.8, f"{a:.0f}%", ha="center", fontsize=8, color=style.TEXT_2)
        ax.text(i + 0.19, b + 0.8, f"{b:.0f}%", ha="center", fontsize=8, color=style.TEXT)
    ax.set_xticks(x, [f"Level {l}" for l in p.index])
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_ylim(0, 60)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right")
    ax.set_title("Entry-level employees on overtime leave at 52.6%")
    style.finish(fig, FIGURES / "02_overtime_by_job_level.png", SOURCE)


def fig_odds(odds):
    d = odds.iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5))
    y = np.arange(len(d))
    sig = d.p_value < 0.05
    colors = [style.SERIES[1] if (s and o > 1) else style.SERIES[0] if s else style.NEUTRAL
              for s, o in zip(sig, d.odds_ratio)]
    ax.hlines(y, d.ci_low, d.ci_high, color=colors, linewidth=2)
    ax.scatter(d.odds_ratio, y, color=colors, s=40, zorder=3, edgecolors=style.SURFACE, linewidths=1)
    ax.axvline(1, color=style.TEXT_2, linewidth=1, linestyle="--")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:g}x"))
    ax.set_xticks([0.25, 0.5, 1, 2, 4, 8])
    ax.xaxis.set_minor_formatter(mtick.NullFormatter())
    ax.set_xlim(0.4, 9)
    ax.set_yticks(y, d.feature, fontsize=9)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Odds ratio with 95% CI (log scale). Gray: not significant at p < 0.05")
    ax.set_title("Logistic regression: what raises or lowers the odds of leaving")
    style.finish(fig, FIGURES / "03_odds_ratios.png", SOURCE)


def main():
    style.apply()
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    r = run_sql(con)
    emp = con.execute("SELECT * FROM stg_employees").df()
    odds, summary = fit_model(emp)
    fig_drivers(r["02_attrition_by_factor"])
    fig_overtime_level(r["03_overtime_by_level"])
    fig_odds(odds)
    print(odds.to_string(index=False))
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
