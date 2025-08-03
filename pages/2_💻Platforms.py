import streamlit as st
import pandas as pd
import requests
import snowflake.connector
import plotly.graph_objects as go
import plotly.express as px

# --- Page Config: Tab Title & Icon -------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Axelar : Interchain Transactions Overview",
    page_icon="https://img.cryptorank.io/coins/axelar1663924228506.png",
    layout="wide"
)

# --- Title & Info Messages ---------------------------------------------------------------------------------------------
st.title("🚀Platforms Powered By Axelar")

st.info("📊 Charts initially display data for a default time range. Select a custom range to view results for your desired period.")
st.info("⏳ On-chain data retrieval may take a few moments. Please wait while the results load.")

# --- Snowflake Connection ----------------------------------------------------------------------------------------------
conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse="SNOWFLAKE_LEARNING_WH",
    database="AXELAR",
    schema="PUBLIC"
)

# --- Time Frame & Period Selection --------------------------------------------------------------------------------------
timeframe = st.selectbox("Select Time Frame", ["month", "week", "day"])
start_date = st.date_input("Start Date", value=pd.to_datetime("2023-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("2025-07-31"))

# --- Load data from Dune API ---
@st.cache_data(ttl=3600)
def load_data():
    url = "https://api.dune.com/api/v1/query/5575605/results?api_key=kmCBMTxWKBxn6CVgCXhwDvcFL1fBp6rO"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["result"]["rows"])
        df["date"] = pd.to_datetime(df["date"])
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        df["num_txs"] = pd.to_numeric(df["num_txs"], errors="coerce")
        return df
    else:
        st.error(f"Failed to load data. Status code: {response.status_code}")
        return pd.DataFrame(columns=["date", "platform", "volume", "num_txs"])

# --- Load & Filter ---
df = load_data()

# Filter by time period
df = df[
    (df["date"].dt.date >= start_date) &
    (df["date"].dt.date <= end_date)
].copy()

# Add timeframe column
df["timeframe"] = df["date"].dt.to_period(timeframe[0].upper()).dt.to_timestamp()

# --- Row 1: Stacked Bar Charts (per timeframe) ---
st.subheader("📊 Transactions & Volume Over Time (by Platform)")

# Group by timeframe and platform
grouped = df.groupby(["timeframe", "platform"]).agg({
    "num_txs": "sum",
    "volume": "sum"
}).reset_index()

col1, col2 = st.columns(2)

# Transactions
fig_txs = px.bar(
    grouped, x="timeframe", y="num_txs", color="platform",
    title="Stacked Transactions Over Time", barmode="stack"
)
col1.plotly_chart(fig_txs, use_container_width=True)

# Volume
fig_vol = px.bar(
    grouped, x="timeframe", y="volume", color="platform",
    title="Stacked Volume Over Time", barmode="stack"
)
col2.plotly_chart(fig_vol, use_container_width=True)

# --- Row 2: Cumulative Line Charts ---
st.subheader("📈 Cumulative Transactions & Volume Over Time")

# Sort for cumulative sum
df_sorted = df.sort_values(by=["platform", "timeframe"])

# Cumulative sum
df_sorted["cum_volume"] = df_sorted.groupby("platform")["volume"].cumsum()
df_sorted["cum_txs"] = df_sorted.groupby("platform")["num_txs"].cumsum()

col3, col4 = st.columns(2)

# Cumulative volume
fig_cum_vol = px.line(
    df_sorted, x="timeframe", y="cum_volume", color="platform",
    title="Cumulative Volume Over Time"
)
col3.plotly_chart(fig_cum_vol, use_container_width=True)

# Cumulative transactions
fig_cum_txs = px.line(
    df_sorted, x="timeframe", y="cum_txs", color="platform",
    title="Cumulative Transactions Over Time"
)
col4.plotly_chart(fig_cum_txs, use_container_width=True)

# --- Row 3: Sorted Bar Charts (Total per Platform) ---
st.subheader("📦 Total Transactions & Volume by Platform (Filtered by Time Period)")

# Aggregate total per platform
total_by_platform = df.groupby("platform").agg({
    "num_txs": "sum",
    "volume": "sum"
}).reset_index()

# Sort
total_txs_sorted = total_by_platform.sort_values(by="num_txs", ascending=False)
total_vol_sorted = total_by_platform.sort_values(by="volume", ascending=False)

col5, col6 = st.columns(2)

# Bar chart: Total Transactions
fig_total_txs = px.bar(
    total_txs_sorted,
    x="platform", y="num_txs", text="num_txs",
    color="platform", title="Total Transactions per Platform"
)
fig_total_txs.update_traces(textposition="outside")
fig_total_txs.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
col5.plotly_chart(fig_total_txs, use_container_width=True)

# Bar chart: Total Volume
fig_total_vol = px.bar(
    total_vol_sorted,
    x="platform", y="volume", text="volume",
    color="platform", title="Total Volume per Platform"
)
fig_total_vol.update_traces(textposition="outside")
fig_total_vol.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
col6.plotly_chart(fig_total_vol, use_container_width=True)
