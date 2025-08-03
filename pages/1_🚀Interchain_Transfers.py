import streamlit as st
import pandas as pd
import requests
import snowflake.connector
import plotly.express as px
import plotly.graph_objects as go

# --- Page Config: Tab Title & Icon -------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Axelar : Interchain Transactions Overview",
    page_icon="https://img.cryptorank.io/coins/axelar1663924228506.png",
    layout="wide"
)

# --- Title with Logo ---------------------------------------------------------------------------------------------------
st.title("🚀Interchain Transfers")

st.info("📊Charts initially display data for a default time range. Select a custom range to view results for your desired period.")
st.info("⏳On-chain data retrieval may take a few moments. Please wait while the results load.")

# --- Snowflake Connection --------------------------------------------------------------------------------------------------
conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse="SNOWFLAKE_LEARNING_WH",
    database="AXELAR",
    schema="PUBLIC"
)

# --- Time Frame & Period Selection ---
timeframe = st.selectbox("Select Time Frame", ["month", "week", "day"])
start_date = st.date_input("Start Date", value=pd.to_datetime("2023-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("2025-07-31"))

# --- Query Functions ---------------------------------------------------------------------------------------
# --- Row 1, 2, 3: Load Additional Dune API Data ---------------------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_volume_data():
    url = "https://api.dune.com/api/v1/query/5574227/results?api_key=kmCBMTxWKBxn6CVgCXhwDvcFL1fBp6rO"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["result"]["rows"])
        df["day"] = pd.to_datetime(df["day"])
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        df["num_txs"] = pd.to_numeric(df["num_txs"], errors="coerce")
        return df
    else:
        st.error(f"Failed to fetch volume data: {response.status_code}")
        return pd.DataFrame(columns=["day", "volume", "num_txs", "service"])

# --- Load Data ----------------------------------------------------------------------------------------
volume_df = load_volume_data()
# ------------------------------------------------------------------------------------------------------
# --- Apply time filter ---
filtered_df = volume_df[(volume_df["day"] >= pd.to_datetime(start_date)) & (volume_df["day"] <= pd.to_datetime(end_date))]

# --- Aggregate by selected timeframe ---
def aggregate_by_time(df, time_col="day", time_frame="day"):
    df = df.copy()
    if time_frame == "week":
        df["time_period"] = df[time_col].dt.to_period("W").apply(lambda r: r.start_time)
    elif time_frame == "month":
        df["time_period"] = df[time_col].dt.to_period("M").apply(lambda r: r.start_time)
    else:
        df["time_period"] = df[time_col]
    return df

agg_df = aggregate_by_time(filtered_df, time_frame=timeframe)

# ---------------------- Row 1: KPIs (num_txs) ----------------------
col1, col2 = st.columns(2)
with col1:
    gmp_txs = agg_df[agg_df["service"] == "GMP"]["num_txs"].sum()
    st.metric("📨 Total GMP Transactions", f"{gmp_txs:,.0f}")

with col2:
    token_txs = agg_df[agg_df["service"] == "Token Transfers"]["num_txs"].sum()
    st.metric("💸 Total Token Transfers Transactions", f"{token_txs:,.0f}")

# ---------------------- Row 2: KPIs (volume) ----------------------
col3, col4 = st.columns(2)
with col3:
    gmp_vol = agg_df[agg_df["service"] == "GMP"]["volume"].sum()
    st.metric("📦 Total GMP Volume", f"${gmp_vol:,.0f}")

with col4:
    token_vol = agg_df[agg_df["service"] == "Token Transfers"]["volume"].sum()
    st.metric("🔁 Total Token Transfers Volume", f"${token_vol:,.0f}")

# ---------------------- Row 3: Charts ----------------------
grouped_df = agg_df.groupby(["time_period", "service"]).agg({
    "num_txs": "sum"
}).reset_index()

pivot_df = grouped_df.pivot(index="time_period", columns="service", values="num_txs").fillna(0)
pivot_df = pivot_df.sort_index()

# Fill missing service columns if not present
for svc in ["GMP", "Token Transfers"]:
    if svc not in pivot_df.columns:
        pivot_df[svc] = 0

col5, col6 = st.columns(2)

# --- Stacked Bar Chart ---
with col5:
    fig_stack = go.Figure()
    fig_stack.add_trace(go.Bar(x=pivot_df.index, y=pivot_df["GMP"], name="GMP"))
    fig_stack.add_trace(go.Bar(x=pivot_df.index, y=pivot_df["Token Transfers"], name="Token Transfers"))
    fig_stack.update_layout(
        barmode="stack",
        title="📊 Stacked TXs Count by Service",
        xaxis_title="Date",
        yaxis_title="TXs Count"
    )
    st.plotly_chart(fig_stack, use_container_width=True)

# --- Normalized Stacked Bar Chart ---
with col6:
    pivot_norm = pivot_df.div(pivot_df.sum(axis=1), axis=0)
    fig_norm = go.Figure()
    fig_norm.add_trace(go.Bar(x=pivot_norm.index, y=pivot_norm["GMP"], name="GMP"))
    fig_norm.add_trace(go.Bar(x=pivot_norm.index, y=pivot_norm["Token Transfers"], name="Token Transfers"))
    fig_norm.update_layout(
        barmode="stack",
        title="📊 Normalized TXs Distribution by Service",
        xaxis_title="Date",
        yaxis_title="Share",
        yaxis=dict(tickformat=".0%")
    )
    st.plotly_chart(fig_norm, use_container_width=True)
