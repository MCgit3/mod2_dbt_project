import streamlit as st
import pandas as pd
import plotly.express as px
from google.cloud import bigquery

#test trigger


# --------------------------------------------------
# Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Olist E-Commerce Dashboard",
    page_icon="🛒",
    layout="wide"
)

PROJECT_ID = "hale-badge-505304-j8"
DATASET = "olist_dataset_mod2"


# --------------------------------------------------
# BigQuery connection
# --------------------------------------------------

@st.cache_resource
def get_client():
    return bigquery.Client(project=PROJECT_ID)


client = get_client()


@st.cache_data
def run_query(query):
    return client.query(query).to_dataframe()


# --------------------------------------------------
# Load data
# --------------------------------------------------

fact_orders = run_query(f"""
SELECT *
FROM `{PROJECT_ID}.{DATASET}.fact_orders`
""")

fact_payments = run_query(f"""
SELECT *
FROM `{PROJECT_ID}.{DATASET}.fact_payments`
""")


# --------------------------------------------------
# Prepare data
# --------------------------------------------------

fact_orders["order_date"] = pd.to_datetime(
    fact_orders["order_date"]
)


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("🛒 Olist E-Commerce Dashboard")

st.markdown(
    """
    Interactive analysis of Olist e-commerce performance
    using curated dbt models in BigQuery.
    """
)


# --------------------------------------------------
# KPIs
# --------------------------------------------------

total_orders = fact_orders["order_id"].nunique()

total_customers = fact_orders["customer_id"].nunique()

total_revenue = fact_orders["total_item_value"].sum()

average_order_value = (
    total_revenue / total_orders
)


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Orders",
    f"{total_orders:,}"
)

col2.metric(
    "Customers",
    f"{total_customers:,}"
)

col3.metric(
    "Revenue",
    f"${total_revenue:,.0f}"
)

col4.metric(
    "Average Order Value",
    f"${average_order_value:,.2f}"
)


# --------------------------------------------------
# Revenue trend
# --------------------------------------------------

st.subheader("Revenue Trend")

monthly_sales = (
    fact_orders
    .set_index("order_date")
    .resample("ME")["total_item_value"]
    .sum()
    .reset_index()
)

fig = px.line(
    monthly_sales,
    x="order_date",
    y="total_item_value",
    markers=True,
    title="Monthly Revenue"
)

fig.update_layout(
    xaxis_title="Month",
    yaxis_title="Revenue"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# --------------------------------------------------
# Order trend
# --------------------------------------------------

st.subheader("Order Volume")

monthly_orders = (
    fact_orders
    .set_index("order_date")
    .resample("ME")["order_id"]
    .nunique()
    .reset_index(name="orders")
)

fig = px.bar(
    monthly_orders,
    x="order_date",
    y="orders",
    title="Monthly Orders"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# --------------------------------------------------
# Payment analysis
# --------------------------------------------------

st.subheader("Payment Analysis")

payment_analysis = (
    fact_payments
    .groupby("payment_type")
    .agg(
        transactions=("payment_type", "count"),
        revenue=("payment_value", "sum")
    )
    .reset_index()
)

fig = px.bar(
    payment_analysis,
    x="payment_type",
    y="revenue",
    color="payment_type",
    title="Payment Value by Payment Type"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# --------------------------------------------------
# Customer analysis
# --------------------------------------------------

st.subheader("Customer Analysis")

customer_sales = (
    fact_orders
    .groupby("customer_id")
    .agg(
        orders=("order_id", "nunique"),
        revenue=("total_item_value", "sum")
    )
    .reset_index()
)

top_customers = (
    customer_sales
    .sort_values(
        "revenue",
        ascending=False
    )
    .head(10)
)

st.dataframe(
    top_customers,
    use_container_width=True
)

st.sidebar.header("Filters")

min_date = fact_orders["order_date"].min()
max_date = fact_orders["order_date"].max()

date_range = st.sidebar.date_input(
    "Order Date",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date()
)

if len(date_range) == 2:

    start_date, end_date = date_range

    filtered_orders = fact_orders[
        (fact_orders["order_date"].dt.date >= start_date) &
        (fact_orders["order_date"].dt.date <= end_date)
    ]

else:

    filtered_orders = fact_orders