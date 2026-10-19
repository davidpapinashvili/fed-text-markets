"""
Interactive figures for the post "Were houses more affordable in 2008 than in 2023?"

Run from the project root:
    python scripts/housing_make_interactive_figures.py

Reads:  posts/houses-2008-2023/data/affordability_annual.csv
        posts/houses-2008-2023/data/hpi_monthly_2016.csv
Writes: output/interactive_figures/housing_*.html
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DATA_DIR = Path("posts/houses-2008-2023/data")
FIGURES_DIR = Path("output/interactive_figures")

# One colour per quantity, used the same way in every chart
PRICE = "#A23B2A"   # house prices
INCOME = "#2F5D8A"  # income per head
INK = "#1F2A36"     # the ratio
MUTED = "#8A94A0"   # reference lines and notes
BAND = "#EEF0F3"    # shaded period


def save(fig, filename):
    fig.write_html(FIGURES_DIR / filename, include_plotlyjs="cdn", full_html=True)
    print(f"Saved: {filename}")


def load_annual():
    df = pd.read_csv(DATA_DIR / "affordability_annual.csv")
    df["ratio"] = df["avg_house_price"] / df["gdhi_per_head"]

    # Real terms: restate every year in 2023 pounds using CPI
    cpi_2023 = df.loc[df["year"] == 2023, "cpi"].item()
    df["real_price"] = df["avg_house_price"] * cpi_2023 / df["cpi"]
    df["real_income"] = df["gdhi_per_head"] * cpi_2023 / df["cpi"]
    return df


def ratio_over_time(annual):
    pair = annual[annual["year"].isin([2008, 2023])].set_index("year")["ratio"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=annual["year"],
        y=annual["ratio"],
        mode="lines+markers",
        line=dict(color=INK, width=2.5),
        marker=dict(color=INK, size=6),
        customdata=annual[["avg_house_price", "gdhi_per_head"]],
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Ratio: %{y:.2f}<br>"
            "Average house price: £%{customdata[0]:,.0f}<br>"
            "Income per head: £%{customdata[1]:,.0f}"
            "<extra></extra>"
        ),
    ))

    # The two matching years, joined by a dotted reference line
    fig.add_shape(type="line", x0=2008, x1=2023, y0=pair.mean(), y1=pair.mean(),
                  line=dict(color=MUTED, width=1.5, dash="dot"), layer="below")
    fig.add_trace(go.Scatter(
        x=pair.index, y=pair.values, mode="markers",
        marker=dict(color=INK, size=13, line=dict(color="white", width=2)),
        hoverinfo="skip",
    ))
    fig.add_annotation(x=2008, y=pair[2008], text=f"2008: {pair[2008]:.2f}", showarrow=False,
                       xanchor="left", yanchor="bottom", xshift=8, yshift=4)
    fig.add_annotation(x=2023, y=pair[2023], text=f"2023: {pair[2023]:.2f}", showarrow=False,
                       xanchor="left", xshift=10)

    # Referendum, 23 June 2016, roughly halfway through the year
    fig.add_shape(type="line", x0=2016.47, x1=2016.47, y0=0, y1=1, yref="paper",
                  line=dict(color=MUTED, width=1, dash="dash"))
    fig.add_annotation(x=2016.47, y=1, yref="paper", text="Brexit vote", showarrow=False,
                       xanchor="left", yanchor="top", xshift=6, font=dict(color=MUTED))

    fig.update_layout(
        title=dict(text="The ratio in 2023 almost exactly matched 2008"
                        "<br><sup>Average UK house price ÷ disposable income per head, 2003 to 2023</sup>"),
        template="plotly_white",
        height=520,
        showlegend=False,
        xaxis=dict(range=[2002.5, 2025.5], tick0=2003, dtick=4, showgrid=False),
        yaxis=dict(title="House price ÷ income per head", range=[8.6, 11.6], tickformat=".1f"),
    )
    save(fig, "housing_ratio_over_time.html")


def cash_vs_real(annual):
    by_year = annual.set_index("year")
    episodes = [(2008, 2009), (2022, 2023)]
    labels = [f"{start} to {end}" for start, end in episodes]

    def growth(col, start, end):
        return (by_year.loc[end, col] / by_year.loc[start, col] - 1) * 100

    panels = [("avg_house_price", "gdhi_per_head"), ("real_price", "real_income")]
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.06,
                        subplot_titles=("In cash terms", "After inflation"))

    for col, (price_col, income_col) in enumerate(panels, start=1):
        for name, series, colour in [("House prices", price_col, PRICE),
                                     ("Income per head", income_col, INCOME)]:
            values = [growth(series, *e) for e in episodes]
            fig.add_trace(go.Bar(
                x=labels,
                y=values,
                name=name,
                marker_color=colour,
                text=[f"{v:+.1f}%" for v in values],
                textposition="outside",
                cliponaxis=False,
                legendgroup=name,
                showlegend=(col == 1),
                hovertemplate=f"<b>{name}</b><br>" + "%{x}: %{y:+.1f}%<extra></extra>",
            ), row=1, col=col)

    fig.update_layout(
        title=dict(text="After inflation, 2009 and 2023 look like the same event"
                        "<br><sup>Annual change in house prices and in income per head</sup>"),
        template="plotly_white",
        height=520,
        barmode="group",
        margin=dict(t=110),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.12),
    )
    fig.update_yaxes(ticksuffix="%", range=[-14, 11], zeroline=True,
                     zerolinecolor=INK, zerolinewidth=1)
    fig.update_yaxes(title_text="Change over the year", row=1, col=1)
    save(fig, "housing_price_vs_income.html")


def monthly_2016(monthly):
    p = monthly["avg_house_price"]
    first = p.iloc[5] / p.iloc[0] - 1
    second = p.iloc[11] / p.iloc[5] - 1
    share = (p.iloc[5] - p.iloc[0]) / (p.iloc[11] - p.iloc[0])

    vote = pd.Timestamp("2016-06-23")
    band_end = pd.Timestamp("2016-08-16")   # midway between the August and September points

    fig = go.Figure()

    # Sales take months to complete, so July and August mostly reflect pre-vote deals
    fig.add_shape(type="rect", x0=vote, x1=band_end, y0=0, y1=1, yref="paper",
                  fillcolor=BAND, line_width=0, layer="below")
    fig.add_shape(type="line", x0=vote, x1=vote, y0=0, y1=1, yref="paper",
                  line=dict(color=MUTED, width=1, dash="dash"))

    fig.add_trace(go.Scatter(
        x=monthly["date"],
        y=p,
        mode="lines+markers",
        line=dict(color=INK, width=2.5),
        marker=dict(color=INK, size=7),
        hovertemplate="<b>%{x|%B %Y}</b><br>Average price: £%{y:,.0f}<extra></extra>",
    ))

    fig.add_annotation(x=vote, y=1, yref="paper", text="Referendum, 23 June", showarrow=False,
                       xanchor="left", yanchor="top", xshift=6, font=dict(color=MUTED))
    fig.add_annotation(x=vote, y=0, yref="paper", showarrow=False, align="left",
                       text="Sales completing here were<br>mostly agreed before the vote",
                       xanchor="left", yanchor="bottom", xshift=6, yshift=6,
                       font=dict(color=MUTED, size=11))
    fig.add_annotation(x=pd.Timestamp("2016-03-10"), y=195_300, showarrow=False,
                       text=f"January to June<br><b>{first:+.1%}</b>")
    fig.add_annotation(x=pd.Timestamp("2016-10-20"), y=195_500, showarrow=False,
                       text=f"June to December<br><b>{second:+.1%}</b>")

    fig.update_layout(
        title=dict(text=f"{share:.0%} of 2016's price rise came before the vote"
                        "<br><sup>Average UK house price by month, 2016</sup>"),
        template="plotly_white",
        height=520,
        showlegend=False,
        xaxis=dict(dtick="M1", tickformat="%b", showgrid=False,
                   range=[pd.Timestamp("2015-12-12"), pd.Timestamp("2016-12-20")]),
        yaxis=dict(title="Average UK house price", tickprefix="£", tickformat="~s",
                   range=[188_000, 200_000]),
    )
    save(fig, "housing_2016_monthly.html")


def main():
    for name in ["affordability_annual.csv", "hpi_monthly_2016.csv"]:
        if not (DATA_DIR / name).exists():
            raise FileNotFoundError(
                f"Input file not found: {DATA_DIR / name}. Run this script from the project root."
            )

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    annual = load_annual()
    monthly = pd.read_csv(DATA_DIR / "hpi_monthly_2016.csv", parse_dates=["date"])

    ratio_over_time(annual)
    cash_vs_real(annual)
    monthly_2016(monthly)

    print(f"\nSaved interactive figures to {FIGURES_DIR.resolve()}")


if __name__ == "__main__":
    main()
