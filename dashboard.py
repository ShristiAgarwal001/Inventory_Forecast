"""Simple Streamlit dashboard for Retail Inventory Analytics."""

from pathlib import Path

import pandas as pd
import streamlit as st


# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent

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


# --------------------------------------------------
# 3. DASHBOARD CSS
# --------------------------------------------------

st.markdown(
    """
    <style>
        /* Main background and text */
        .stApp {
            background-color: #f7f8fa !important;
            color: #20252b !important;
        }

        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            background-color: #f7f8fa !important;
        }

        [data-testid="stHeader"] {
            background-color: #f7f8fa !important;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        /* Main headings */
        .stApp h1,
        .stApp h2,
        .stApp h3,
        [data-testid="stHeading"] h1,
        [data-testid="stHeading"] h2,
        [data-testid="stHeading"] h3 {
            color: #172033 !important;
            opacity: 1 !important;
            visibility: visible !important;
        }

        /* Normal text */
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] strong,
        [data-testid="stCaptionContainer"] p {
            color: #344054 !important;
            opacity: 1 !important;
        }

        /* Metric cards */
        [data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #d9dfe7 !important;
            border-radius: 6px !important;
            padding: 16px !important;
            opacity: 1 !important;
            visibility: visible !important;
        }

        /* Metric labels */
        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] *,
        [data-testid="stMetricLabel"] p {
            color: #344054 !important;
            -webkit-text-fill-color: #344054 !important;
            opacity: 1 !important;
            visibility: visible !important;
        }

        /* Metric numbers */
        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] *,
        [data-testid="stMetricValue"] div {
            color: #172033 !important;
            -webkit-text-fill-color: #172033 !important;
            opacity: 1 !important;
            visibility: visible !important;
        }

        /* Metric delta, if displayed */
        [data-testid="stMetricDelta"],
        [data-testid="stMetricDelta"] * {
            opacity: 1 !important;
            visibility: visible !important;
        }

        /* Section headings */
        .section-heading {
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

        /* Tabs */
        [data-testid="stTabs"] button,
        [data-baseweb="tab"] {
            color: #20252b !important;
            opacity: 1 !important;
        }

        /* Select box labels */
        [data-testid="stSelectbox"] label {
            color: #20252b !important;
        }

        /* Dividers */
        hr {
            border-color: #d9dfe7 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# 4. SECTION HEADING FUNCTION
# --------------------------------------------------

def section_heading(title):
    """Display a clearly visible section heading."""

    st.markdown(
        f'<div class="section-heading">{title}</div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# 5. DASHBOARD HEADER
# --------------------------------------------------

st.title("Retail Inventory Analytics")

st.caption(
    "Sales, demand, inventory status and forecast performance"
)

st.divider()


# --------------------------------------------------
# 6. LOAD DATA
# --------------------------------------------------

csv_path = next(
    (path for path in DATA_PATHS if path.exists()),
    None,
)

if csv_path is None:
    st.warning(
        "Cleaned dataset was not found. "
        "Run python main.py first to generate the cleaned dataset."
    )
    st.stop()

try:
    df = pd.read_csv(csv_path)

except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
    st.error(f"Could not read the dataset: {exc}")
    st.stop()


# --------------------------------------------------
# 7. VALIDATE COLUMNS
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

missing_columns = required_columns - set(df.columns)

if missing_columns:
    st.error(
        "The dataset is missing these columns: "
        + ", ".join(sorted(missing_columns))
    )
    st.stop()


# --------------------------------------------------
# 8. DATA PREPROCESSING
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

df = df.dropna(
    subset=["Units Sold", "Price"]
).copy()

if df.empty:
    st.warning("No valid records are available in the dataset.")
    st.stop()

# Calculate revenue using the existing dataset columns.
df["Total Revenue"] = (
    df["Units Sold"]
    * df["Price"]
    * (1 - df["Discount"].fillna(0) / 100)
)


# --------------------------------------------------
# 9. PRODUCT SUMMARY
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

# Existing stock classification rules.
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
    st.metric(
        label="Total Revenue",
        value=f"${total_revenue:,.2f}",
    )

with k2:
    st.metric(
        label="Units Sold",
        value=f"{total_units:,.0f}",
    )

with k3:
    st.metric(
        label="Average Unit Price",
        value=f"${average_price:,.2f}",
    )

with k4:
    st.metric(
        label="Forecast MAE",
        value=(
            f"{mae:,.2f} units"
            if pd.notna(mae)
            else "N/A"
        ),
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
    st.metric(
        label="Under-stocked Products",
        value=f"{under_count:,}",
    )

with s2:
    st.metric(
        label="Optimal Stock",
        value=f"{optimal_count:,}",
    )

with s3:
    st.metric(
        label="Over-stocked Products",
        value=f"{over_count:,}",
    )

st.caption(
    "Under-stocked: inventory below 3 times average daily demand. "
    "Over-stocked: inventory above 15 times average daily demand."
)


# --------------------------------------------------
# 13. CHARTS
# --------------------------------------------------

section_heading("Charts")

chart_left, chart_right = st.columns(2)


# Chart 1: Daily Demand and Moving Average

daily_demand = (
    df.groupby("Date", as_index=False)["Units Sold"]
    .sum()
    .sort_values("Date")
)

daily_demand["7-Day Moving Average"] = (
    daily_demand["Units Sold"]
    .rolling(window=7, min_periods=1)
    .mean()
)

with chart_left:
    st.markdown("**Daily Demand and 7-Day Moving Average**")

    st.line_chart(
        daily_demand.set_index("Date")[
            ["Units Sold", "7-Day Moving Average"]
        ],
        use_container_width=True,
    )


# Chart 2: Revenue by Category

category_revenue = (
    df.groupby("Category", as_index=False)["Total Revenue"]
    .sum()
    .sort_values("Total Revenue", ascending=False)
)

with chart_right:
    st.markdown("**Revenue by Category**")

    st.bar_chart(
        category_revenue.set_index("Category")[["Total Revenue"]],
        use_container_width=True,
    )


# Chart 3: Top 10 Products by Demand

chart_left, chart_right = st.columns(2)

top_products = (
    product_summary
    .sort_values("Total_Demand", ascending=False)
    .head(10)
    .sort_values("Total_Demand", ascending=True)
)

with chart_left:
    st.markdown("**Top 10 Products by Demand**")

    st.bar_chart(
        top_products.set_index("Product ID")[["Total_Demand"]],
        use_container_width=True,
    )


# Chart 4: Actual Demand vs Forecast

daily_forecast = (
    df.groupby("Date", as_index=False)[
        ["Units Sold", "Demand Forecast"]
    ]
    .sum(min_count=1)
    .sort_values("Date")
)

with chart_right:
    st.markdown("**Actual Demand vs Forecast**")

    st.line_chart(
        daily_forecast.set_index("Date")[
            ["Units Sold", "Demand Forecast"]
        ],
        use_container_width=True,
    )


# Chart 5: Units Sold by Seasonality

chart_left, chart_right = st.columns(2)

seasonal_units = (
    df.groupby("Seasonality", as_index=False)["Units Sold"]
    .sum()
    .sort_values("Units Sold", ascending=False)
)

with chart_left:
    st.markdown("**Units Sold by Seasonality**")

    st.bar_chart(
        seasonal_units.set_index("Seasonality")[["Units Sold"]],
        use_container_width=True,
    )


# Chart 6: Units Sold by Category

category_demand = (
    df.groupby("Category", as_index=False)["Units Sold"]
    .sum()
    .sort_values("Units Sold", ascending=False)
)

with chart_right:
    st.markdown("**Units Sold by Category**")

    st.bar_chart(
        category_demand.set_index("Category")[["Units Sold"]],
        use_container_width=True,
    )


# --------------------------------------------------
# 14. FORECAST CHECK
# --------------------------------------------------

section_heading("Forecast Check")

scatter_data = forecast_rows[
    ["Demand Forecast", "Units Sold"]
].dropna()

if not scatter_data.empty:

    if len(scatter_data) > 1000:
        scatter_data = scatter_data.sample(
            n=1000,
            random_state=42,
        )

    st.markdown("**Forecasted Units vs Actual Units**")

    st.scatter_chart(
        scatter_data,
        x="Demand Forecast",
        y="Units Sold",
        use_container_width=True,
    )

else:
    st.info(
        "No data is available for forecast comparison."
    )


# --------------------------------------------------
# 15. PRODUCT DEMAND TABLES
# --------------------------------------------------

section_heading("Product Demand")

tab1, tab2, tab3 = st.tabs(
    [
        "Highest Demand",
        "Lowest Demand",
        "Stock Status",
    ]
)


# Highest demand products
with tab1:
    highest_demand = (
        product_summary
        .sort_values("Total_Demand", ascending=False)
        .head(10)
        .round(2)
    )

    st.dataframe(
        highest_demand,
        use_container_width=True,
        hide_index=True,
    )


# Lowest demand products
with tab2:
    lowest_demand = (
        product_summary
        .sort_values("Total_Demand", ascending=True)
        .head(10)
        .round(2)
    )

    st.dataframe(
        lowest_demand,
        use_container_width=True,
        hide_index=True,
    )


# Filter products by stock status
with tab3:
    status_filter = st.selectbox(
        "Filter by Stock Status",
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
        .sort_values("Total_Demand", ascending=False)
        .round(2),
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# 16. FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    f"Data period: {df['Date'].min():%d %b %Y} - "
    f"{df['Date'].max():%d %b %Y} | "
    f"Records: {len(df):,}"
)