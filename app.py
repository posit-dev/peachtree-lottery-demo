import os

import pandas as pd
import plotly.graph_objects as go

from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget

from create_lottery_map import create_lottery_map

# ── Working directory ─────────────────────────────────────────────────────────
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ── Data ──────────────────────────────────────────────────────────────────────
georgia_lottery: pd.DataFrame = pd.read_parquet("georgia_lottery.parquet")
georgia_lottery["year"] = georgia_lottery["year"].astype(int)
for _col in ["sex", "race_ethnicity", "income_level", "age_group"]:
    georgia_lottery[_col] = georgia_lottery[_col].astype(str)

# Ordered categories for axes
INCOME_ORDER = ["Under $15K", "$15K-$30K", "$30K-$50K", "$50K-$75K", "$75K-$100K", "$100K-$150K", "$150K+"]
AGE_ORDER = ["20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]

# ── Choice lists ──────────────────────────────────────────────────────────────
_years = sorted(georgia_lottery["year"].unique().tolist())
_sexes = sorted(georgia_lottery["sex"].unique().tolist())
_races = sorted(georgia_lottery["race_ethnicity"].unique().tolist())
_incomes = sorted(
    georgia_lottery["income_level"].unique().tolist(),
    key=lambda x: INCOME_ORDER.index(x) if x in INCOME_ORDER else 999,
)
_ages = sorted(
    georgia_lottery["age_group"].unique().tolist(),
    key=lambda x: AGE_ORDER.index(x) if x in AGE_ORDER else 999,
)

# ── Theme / CSS ───────────────────────────────────────────────────────────────
_brand_green = "#9fbe93"
_custom_css = f"""
.navbar, .navbar-default {{
    background-color: {_brand_green} !important;
    border-color: {_brand_green} !important;
}}
.navbar-brand, .navbar-title {{
    color: #ffffff !important;
}}
.card-header {{
    background-color: {_brand_green} !important;
    color: #ffffff !important;
    border-color: {_brand_green} !important;
}}
"""

# ── UI ────────────────────────────────────────────────────────────────────────
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select(
            "year",
            "Year",
            choices={str(y): str(y) for y in _years},
            selected=[str(max(_years))],
            multiple=True,
        ),
        ui.input_select(
            "sex",
            "Sex",
            choices=["All"] + _sexes,
            selected=["All"],
            multiple=True,
        ),
        ui.input_select(
            "race",
            "Race / Ethnicity",
            choices=["All"] + _races,
            selected=["All"],
            multiple=True,
        ),
        ui.input_select(
            "income",
            "Income Level",
            choices=["All"] + _incomes,
            selected=["All"],
            multiple=True,
        ),
        ui.input_select(
            "age",
            "Age Group",
            choices=["All"] + _ages,
            selected=["All"],
            multiple=True,
        ),
        width=230,
    ),
    ui.tags.style(_custom_css),
    ui.layout_columns(
        # Left column — map
        ui.card(
            ui.card_header("Per Capita Lottery Sales"),
            ui.output_ui("map"),
            full_screen=True,
        ),
        # Right column — 2x2 grid of charts
        ui.layout_columns(
            ui.card(
                ui.card_header("Lottery Spend by Sex"),
                output_widget("sex_plot"),
            ),
            ui.card(
                ui.card_header("Lottery Spend by Race/Ethnicity"),
                output_widget("race_plot"),
            ),
            ui.card(
                ui.card_header("Lottery Spend by Age Group"),
                output_widget("age_plot"),
            ),
            ui.card(
                ui.card_header("Lottery Spend by Income Level"),
                output_widget("income_plot"),
            ),
            col_widths=[6, 6],
        ),
        col_widths=[6, 6],
    ),
    title="2025 Georgia Lottery Sales",
    theme=ui.Theme("cosmo"),
)


# ── Server ────────────────────────────────────────────────────────────────────
def server(input, output, session):

    @reactive.calc
    def filtered_data() -> pd.DataFrame:
        df = georgia_lottery.copy()

        years_sel = list(input.year())
        if years_sel:
            df = df[df["year"].isin([int(y) for y in years_sel])]

        sex_sel = list(input.sex())
        if sex_sel and "All" not in sex_sel:
            df = df[df["sex"].isin(sex_sel)]

        race_sel = list(input.race())
        if race_sel and "All" not in race_sel:
            df = df[df["race_ethnicity"].isin(race_sel)]

        income_sel = list(input.income())
        if income_sel and "All" not in income_sel:
            df = df[df["income_level"].isin(income_sel)]

        age_sel = list(input.age())
        if age_sel and "All" not in age_sel:
            df = df[df["age_group"].isin(age_sel)]

        return df

    @render.ui
    def map():
        m = create_lottery_map(filtered_data(), per_capita=True)
        return ui.HTML(m._repr_html_())

    @render_widget
    def sex_plot():
        df = filtered_data()
        sex_totals = df.groupby("sex", as_index=False)["lottery_spend"].sum()
        fig = go.Figure(
            go.Pie(
                labels=sex_totals["sex"],
                values=sex_totals["lottery_spend"],
                hole=0.5,
                marker=dict(
                    colors=["#4393c3", "#d6604d"],
                    line=dict(color="white", width=2),
                ),
                textinfo="label+percent",
                textfont=dict(size=14, color="white"),
            )
        )
        fig.update_layout(
            showlegend=False,
            margin=dict(t=0, b=0, l=0, r=0),
            height=270,
        )
        return fig

    @render_widget
    def race_plot():
        df = filtered_data()
        race_totals = df.groupby("race_ethnicity", as_index=False)["lottery_spend"].sum()
        race_colors = [
            "#4393c3", "#d6604d", "#74c476", "#9e9ac8",
            "#fdae6b", "#41ab5d", "#f4a582",
        ]
        fig = go.Figure(
            go.Pie(
                labels=race_totals["race_ethnicity"],
                values=race_totals["lottery_spend"],
                hole=0.5,
                marker=dict(
                    colors=race_colors,
                    line=dict(color="white", width=2),
                ),
                textinfo="label+percent",
                textfont=dict(size=12, color="white"),
            )
        )
        fig.update_layout(
            showlegend=False,
            margin=dict(t=0, b=0, l=0, r=0),
            height=270,
        )
        return fig

    @render_widget
    def age_plot():
        df = filtered_data()
        age_totals = (
            df.groupby("age_group", as_index=False)["lottery_spend"]
            .sum()
            .assign(
                age_group=lambda x: pd.Categorical(
                    x["age_group"], categories=AGE_ORDER, ordered=True
                )
            )
            .sort_values("age_group")
        )
        blues = ["#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#084594"]
        n = len(age_totals)
        colors = (blues * ((n // len(blues)) + 1))[:n]

        fig = go.Figure(
            go.Bar(
                x=age_totals["age_group"].astype(str),
                y=age_totals["lottery_spend"] / 1e6,
                marker_color=colors,
                text=[f"${v:.1f}M" for v in age_totals["lottery_spend"] / 1e6],
                textposition="outside",
            )
        )
        fig.update_layout(
            xaxis_title="Age group",
            yaxis_title="Spend (millions)",
            showlegend=False,
            margin=dict(t=20, b=40, l=0, r=0),
            height=270,
            yaxis=dict(tickprefix="$", ticksuffix="M"),
            plot_bgcolor="white",
            yaxis_showgrid=True,
            xaxis_showgrid=False,
        )
        return fig

    @render_widget
    def income_plot():
        df = filtered_data()
        income_totals = (
            df.groupby("income_level", as_index=False)["lottery_spend"]
            .sum()
            .assign(
                income_level=lambda x: pd.Categorical(
                    x["income_level"], categories=INCOME_ORDER, ordered=True
                )
            )
            .sort_values("income_level")
        )
        oranges = ["#feedde", "#fdd0a2", "#fdae6b", "#fd8d3c", "#e6550d", "#a63603"]
        n = len(income_totals)
        colors = (oranges * ((n // len(oranges)) + 1))[:n]

        fig = go.Figure(
            go.Bar(
                x=income_totals["income_level"].astype(str),
                y=income_totals["lottery_spend"] / 1e6,
                marker_color=colors,
                text=[f"${v:.1f}M" for v in income_totals["lottery_spend"] / 1e6],
                textposition="outside",
            )
        )
        fig.update_layout(
            xaxis_title="Income level",
            yaxis_title="Spend (millions)",
            showlegend=False,
            margin=dict(t=20, b=60, l=0, r=0),
            height=270,
            yaxis=dict(tickprefix="$", ticksuffix="M"),
            xaxis=dict(tickangle=30),
            plot_bgcolor="white",
            yaxis_showgrid=True,
            xaxis_showgrid=False,
        )
        return fig


app = App(app_ui, server)
