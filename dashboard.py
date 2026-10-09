"""Simple Streamlit dashboard for Retail Inventory Analytics."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st


# --------------------------------------------------
# 1. PROJECT PATHS AND CONFIGURATION
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = PROJECT_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATA_PATHS = [
    PROJECT_DIR / "data" / "cleandata" /
    "retail_store_inventory_cleaned.csv",

    PROJECT_DIR / "outputs" /
    "retail_store_inventory_cleaned.csv",
]


# --------------------------------------------------
# 2. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Retail Inventory Analytics",
    page_icon="📊",
    layout="wide",
)

sns.set_theme(style="whitegrid")


# --------------------------------------------------
# 3. DASHBOARD STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            background-color: #f7f8fa !important;
            color: #20252b !important;
        }

        [data-testid="stHeader"] {
            background-color: #f7f8fa !important;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        h1, h2, h3,
        [data-testid="stHeading"] h1,
        [data-testid="stHeading"] h2,
        [data-testid="stHeading"] h3 {
            color: #172033 !important;
            opacity: 1 !important;
            visibility: visible !important;
        }

        .section-heading {
            display: block;
            width: 100%;
            box-sizing: border-box;
            background-color: #e8edf3 !important;
            color: #172033 !important;
            border-left: 5px solid #294765;
            padding: 10px 14px;
            margin: 14px 0;
            border-radius: 4px;
            font-size: 22px;
            font-weight: 700;
            line-height: 1.4;
            opacity: 1 !important;
            visibility: visible !important;
        }

        .metric-card {
            min-height: 92px;
            box-sizing: border-box;
            padding: 14px;
            background: #ffffff !important;
            border: 1px solid #d9dfe7;
            border-radius: 6px;
            color: #172033 !important;
        }

        .metric-label {
            color: #4b5563 !important;
            font-size: 14px;
            margin-bottom: 8px;
            opacity: 1 !important;
        }

        .metric-value {
            color: #172033 !important;
            font-size: 25px;
            font-weight: 700;
            line-height: 1.25;
            opacity: 1 !important;
        }

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stCaptionContainer"] p,
        [data-testid="stTabs"] button,
        [data-baseweb="tab"],
        [data-testid="stSelectbox"] label {
            color: #344054 !important;
            opacity: 1 !important;
        }

        hr {
            border-color: #d9dfe7 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# 4. HELPER FUNCTIONS
# --------------------------------------------------

def section_heading(title: str) -> None:
    """Display a clearly visible section heading."""

    st.markdown(
        f'<div class="section-heading">{title}</div>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str) -> None:
    """Display a simple metric card with readable text."""

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_chart(fig, filename: str) -> None:
    """Save and display a chart."""

    fig.tight_layout()

    fig.savefig(
        OUTPUT_DIR / filename,
        dpi=300,
        bbox_inches="tight",
    )

    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


# --------------------------------------------------
# 5. DASHBOARD HEADER
# --------------------------------------------------

st.title("Retail Inventory Analytics")

st.caption(
    "Sales, demand, inventory status and forecast performance"
)

st.divider()


# --------------------------------------------------
# 6. LOAD CLEANED DATASET
# --------------------------------------------------

csv_path = next(
    (path for path in DATA_PATHS if path.exists()),
    None,
)

if csv_path is None:
    st.warning(
        "Cleaned data was not found. Run python main.py first, "
        "then make sure the cleaned CSV is included in GitHub."
    )
    st.stop()

try:
    df = pd.read_csv(csv_path)

except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
    st.error(f"Could not read the cleaned dataset: {exc}")
    st.stop()


# --------------------------------------------------
# 7. VALIDATE REQUIRED COLUMNS
# --------------------------------------------------

required_columns = {
    "Date",
    "Product ID",
    "Units Sold",
    "Price",
    "Discount",
    "Inventory Level",
    "Demand Forecast",
    "Category",
    "Seasonality",
}

missing_columns = sorted(
    required_columns - set(df.columns)
)

if missing_columns:
    st.error(
        "The cleaned dataset is missing required columns: "
        + ", ".join(missing_columns)
    )
    st.stop()


# --------------------------------------------------
# 8. DATA PREPARATION
# --------------------------------------------------

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce",
)

df = df.dropna(subset=["Date"]).copy()

numeric_columns = [
    "Units Sold",
    "Price",
    "Discount",
    "Inventory Level",
    "Demand Forecast",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )

df["Category"] = df["Category"].fillna("Unknown")
df["Seasonality"] = df["Seasonality"].fillna("Unknown")
df["Product ID"] = df["Product ID"].fillna("Unknown")
df["Discount"] = df["Discount"].fillna(0)

df = df.dropna(
    subset=["Units Sold", "Price"]
).copy()

if df.empty:
    st.warning(
        "There are no valid dated sales records in the dataset."
    )
    st.stop()

# Calculate revenue using existing dataset columns.
df["Total Revenue"] = (
    df["Units Sold"]
    * df["Price"]
    * (1 - df["Discount"] / 100)
)


# --------------------------------------------------
# 9. PRODUCT SUMMARY AND INVENTORY STATUS
# --------------------------------------------------

product_summary = (
    df.groupby("Product ID", dropna=False)
    .agg(
        Total_Demand=("Units Sold", "sum"),
        Average_Daily_Demand=("Units Sold", "mean"),
        Current_Inventory=("Inventory Level", "mean"),
        Average_Forecast=("Demand Forecast", "mean"),
    )
    .reset_index()
)

product_summary["Stock Status"] = "Optimal"

product_summary.loc[
    product_summary["Current_Inventory"]
    < product_summary["Average_Daily_Demand"] * 3,
    "Stock Status",
] = "Under-stocked"

product_summary.loc[
    product_summary["Current_Inventory"]
    > product_summary["Average_Daily_Demand"] * 15,
    "Stock Status",
] = "Over-stocked"


# --------------------------------------------------
# 10. FORECAST ERROR
# --------------------------------------------------

forecast_rows = df.dropna(
    subset=["Demand Forecast", "Units Sold"]
)

if forecast_rows.empty:
    mae = float("nan")
else:
    mae = (
        forecast_rows["Units Sold"]
        - forecast_rows["Demand Forecast"]
    ).abs().mean()


# --------------------------------------------------
# 11. OVERVIEW
# --------------------------------------------------

section_heading("Overview")

total_revenue = df["Total Revenue"].sum()
total_units = df["Units Sold"].sum()
average_price = df["Price"].mean()

k1, k2, k3, k4 = st.columns(4)

with k1:
    metric_card(
        "Total Revenue",
        f"${total_revenue:,.2f}",
    )

with k2:
    metric_card(
        "Units Sold",
        f"{total_units:,.0f}",
    )

with k3:
    metric_card(
        "Average Unit Price",
        f"${average_price:,.2f}",
    )

with k4:
    metric_card(
        "Forecast MAE",
        f"{mae:,.2f} units" if pd.notna(mae) else "N/A",
    )


# --------------------------------------------------
# 12. INVENTORY STATUS
# --------------------------------------------------

section_heading("Inventory Status")

under_count = int(
    (product_summary["Stock Status"] == "Under-stocked").sum()
)

optimal_count = int(
    (product_summary["Stock Status"] == "Optimal").sum()
)

over_count = int(
    (product_summary["Stock Status"] == "Over-stocked").sum()
)

s1, s2, s3 = st.columns(3)

with s1:
    metric_card(
        "Under-stocked Products",
        f"{under_count:,}",
    )

with s2:
    metric_card(
        "Optimal Stock",
        f"{optimal_count:,}",
    )

with s3:
    metric_card(
        "Over-stocked Products",
        f"{over_count:,}",
    )

st.caption(
    "Stock status rule: below 3 times average daily demand "
    "is under-stocked; above 15 times is over-stocked."
)


# --------------------------------------------------
# 13. CHARTS
# --------------------------------------------------

section_heading("Charts")

chart_left, chart_right = st.columns(2)


# Chart 1: Revenue by Category
# --------------------------------------------------

category_summary = (
    df.groupby("Category", as_index=False)["Total Revenue"]
    .sum()
    .sort_values("Total Revenue", ascending=False)
)

with chart_left:
    st.markdown(
        "**Total Revenue Distribution by Product Category**"
    )

    if category_summary.empty:
        st.info("No category revenue data is available.")

    else:
        fig, ax = plt.subplots(figsize=(10, 5))

        sns.barplot(
            data=category_summary,
            x="Category",
            y="Total Revenue",
            hue="Category",
            palette="Blues_d",
            legend=False,
            ax=ax,
        )

        for container in ax.containers:
            ax.bar_label(
                container,
                fmt="%.2f",
                padding=3,
                fontsize=8,
            )

        ax.set_title(
            "Total Revenue Distribution by Product Category"
        )
        ax.set_xlabel("Category")
        ax.set_ylabel("Total Revenue ($)")
        ax.tick_params(
            axis="x",
            labelrotation=45,
        )

        display_chart(
            fig,
            "01_category_revenue.png",
        )


# Chart 2: Units Sold by Seasonality
# --------------------------------------------------

seasonal_units = (
    df.groupby("Seasonality")["Units Sold"].sum()
)

with chart_right:
    st.markdown("**Total Units Sold by Seasonality**")

    if seasonal_units.empty or seasonal_units.sum() == 0:
        st.info("No seasonal sales data is available.")

    else:
        fig, ax = plt.subplots(figsize=(6, 6))

        ax.pie(
            seasonal_units,
            labels=seasonal_units.index,
            autopct="%1.1f%%",
            startangle=130,
            colors=sns.color_palette(
                "Set2",
                n_colors=len(seasonal_units),
            ),
        )

        ax.set_title("Total Units Sold by Seasonality")

        display_chart(
            fig,
            "02_seasonal_units_distribution.png",
        )


# Chart 3: Top 10 Demand Products
# --------------------------------------------------

top_10 = (
    product_summary
    .sort_values(
        by="Total_Demand",
        ascending=False,
    )
    .head(10)
)

chart_left, chart_right = st.columns(2)

with chart_left:
    st.markdown("**Top 10 Highest Demand Products**")

    if top_10.empty:
        st.info("No product demand data is available.")

    else:
        fig, ax = plt.subplots(figsize=(12, 6))

        sns.barplot(
            data=top_10,
            x="Total_Demand",
            y="Product ID",
            hue="Product ID",
            palette="viridis",
            legend=False,
            ax=ax,
        )

        for container in ax.containers:
            ax.bar_label(
                container,
                fmt="%.0f",
                padding=3,
                fontsize=8,
            )

        ax.set_title("Top 10 Highest Demand Products")
        ax.set_xlabel("Total Units Sold")
        ax.set_ylabel("Product ID")

        display_chart(
            fig,
            "03_top_demand_products.png",
        )


# Chart 4: Daily Demand and Moving Average
# --------------------------------------------------

daily_demand = (
    df.groupby("Date")["Units Sold"]
    .sum()
    .reset_index()
    .sort_values("Date")
)

daily_demand["7_Day_Moving_Avg"] = (
    daily_demand["Units Sold"]
    .rolling(
        window=7,
        min_periods=1,
    )
    .mean()
)

with chart_right:
    st.markdown(
        "**Daily Total Demand with 7-Day Moving Average**"
    )

    if daily_demand.empty:
        st.info("No daily demand data is available.")

    else:
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(
            daily_demand["Date"],
            daily_demand["Units Sold"],
            alpha=0.3,
            label="Daily Units Sold",
            color="gray",
        )

        ax.plot(
            daily_demand["Date"],
            daily_demand["7_Day_Moving_Avg"],
            label="7-Day Moving Average Trend",
            color="red",
            linewidth=2,
        )

        ax.set_title(
            "Daily Total Demand with 7-Day Moving Average"
        )
        ax.set_xlabel("Date")
        ax.set_ylabel("Units Sold")
        ax.legend()

        display_chart(
            fig,
            "04_demand_trend_7day_moving_avg.png",
        )


# Chart 5: Forecast vs Actual
# --------------------------------------------------

chart_left, chart_right = st.columns(2)

with chart_left:
    st.markdown(
        "**Baseline Demand Forecast vs Actual Units Sold**"
    )

    df_forecast = df.dropna(
        subset=["Demand Forecast", "Units Sold"]
    ).copy()

    if df_forecast.empty:
        st.info(
            "No data is available for forecast comparison."
        )

    else:
        sample_data = df_forecast.sample(
            n=min(1000, len(df_forecast)),
            random_state=42,
        )

        fig, ax = plt.subplots(figsize=(10, 6))

        sns.scatterplot(
            data=sample_data,
            x="Demand Forecast",
            y="Units Sold",
            alpha=0.5,
            color="teal",
            ax=ax,
        )

        max_value = max(
            float(df_forecast["Demand Forecast"].max()),
            float(df_forecast["Units Sold"].max()),
        )

        if pd.notna(max_value) and max_value > 0:
            ax.plot(
                [0, max_value],
                [0, max_value],
                "r--",
                label="Ideal Forecast",
            )

        ax.set_title(
            "Baseline Demand Forecast vs Actual Units Sold"
        )
        ax.set_xlabel("Baseline Forecasted Demand")
        ax.set_ylabel("Actual Units Sold")
        ax.legend()

        display_chart(
            fig,
            "05_forecast_vs_actual.png",
        )


# Chart 6: High-Demand Categories
# --------------------------------------------------

category_demand = (
    df.groupby("Category")["Units Sold"]
    .sum()
    .reset_index()
    .sort_values(
        by="Units Sold",
        ascending=False,
    )
)

with chart_right:
    st.markdown("**High-Demand Product Categories**")

    if category_demand.empty:
        st.info("No category demand data is available.")

    else:
        fig, ax = plt.subplots(figsize=(10, 6))

        sns.barplot(
            data=category_demand,
            x="Category",
            y="Units Sold",
            hue="Category",
            palette="magma",
            legend=False,
            ax=ax,
        )

        for container in ax.containers:
            ax.bar_label(
                container,
                fmt="%.0f",
                padding=3,
                fontsize=8,
            )

        ax.set_title("High-Demand Product Categories")
        ax.set_xlabel("Product Category")
        ax.set_ylabel("Total Units Sold")
        ax.tick_params(
            axis="x",
            labelrotation=45,
        )

        display_chart(
            fig,
            "06_high_demand_categories.png",
        )


# --------------------------------------------------
# 14. PRODUCT DEMAND TABLES
# --------------------------------------------------

section_heading("Product Demand")

tab1, tab2, tab3 = st.tabs(
    [
        "Highest Demand",
        "Lowest Demand",
        "Stock Status",
    ]
)


# Highest-demand products
with tab1:
    st.dataframe(
        product_summary
        .sort_values(
            "Total_Demand",
            ascending=False,
        )
        .head(10)
        .round(2),
        use_container_width=True,
        hide_index=True,
    )


# Lowest-demand products
with tab2:
    st.dataframe(
        product_summary
        .sort_values(
            "Total_Demand",
            ascending=True,
        )
        .head(10)
        .round(2),
        use_container_width=True,
        hide_index=True,
    )


# Stock status filter
with tab3:
    status_filter = st.selectbox(
        "Filter by stock status",
        [
            "All",
            "Under-stocked",
            "Optimal",
            "Over-stocked",
        ],
    )

    if status_filter == "All":
        shown_products = product_summary

    else:
        shown_products = product_summary[
            product_summary["Stock Status"] == status_filter
        ]

    st.dataframe(
        shown_products
        .sort_values(
            "Total_Demand",
            ascending=False,
        )
        .round(2),
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# 15. FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    f"Data period: {df['Date'].min():%d %b %Y} – "
    f"{df['Date'].max():%d %b %Y} | "
    f"Records: {len(df):,}"
)