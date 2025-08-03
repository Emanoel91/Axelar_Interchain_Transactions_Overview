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

# --- Load Data from API ---
@st.cache_data(ttl=3600)
def load_platform_data():
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
        st.error(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame(columns=["date", "volume", "num_txs", "platform"])

# --- Load and Filter ---
df_raw = load_platform_data()
df_filtered = df_raw[
    (df_raw["date"].dt.date >= start_date) &
    (df_raw["date"].dt.date <= end_date)
].copy()

# --- Add Timeframe Column ---
df_filtered["timeframe"] = df_filtered["date"].dt.to_period(timeframe[0].upper()).dt.to_timestamp()

# --- Grouped Data ---
grouped = df_filtered.groupby(["timeframe", "platform"]).agg({
    "num_txs": "sum",
    "volume": "sum"
}).reset_index()

# --- Charts: Transactions Over Time ---
st.subheader("📊 Transactions Over Time by Platform")
col1, col2 = st.columns(2)

fig_txs = px.bar(grouped, x="timeframe", y="num_txs", color="platform", title="Total Transactions")
fig_txs_norm = px.bar(grouped, x="timeframe", y="num_txs", color="platform",
                      title="Normalized Transactions", barmode="stack")
fig_txs_norm.update_layout(barnorm="percent")

col1.plotly_chart(fig_txs, use_container_width=True)
col2.plotly_chart(fig_txs_norm, use_container_width=True)

# --- Charts: Volume Over Time ---
st.subheader("💰 Volume Over Time by Platform")
col3, col4 = st.columns(2)

fig_vol = px.bar(grouped, x="timeframe", y="volume", color="platform", title="Total Volume")
fig_vol_norm = px.bar(grouped, x="timeframe", y="volume", color="platform",
                      title="Normalized Volume", barmode="stack")
fig_vol_norm.update_layout(barnorm="percent")

col3.plotly_chart(fig_vol, use_container_width=True)
col4.plotly_chart(fig_vol_norm, use_container_width=True)

# --- Bar Charts: Total TXs & Volume by Platform ---
st.subheader("📦 Total Transactions & Volume by Platform")

total_summary = df_filtered.groupby("platform").agg({
    "num_txs": "sum",
    "volume": "sum"
}).reset_index()

# --- مرتب‌سازی بر اساس تعداد تراکنش ---
total_txs_sorted = total_summary.sort_values(by="num_txs", ascending=False)
fig_total_txs = px.bar(
    total_txs_sorted,
    x="platform",
    y="num_txs",
    text="num_txs",
    color="platform",
    title="Total Transactions per Platform"
)
fig_total_txs.update_traces(textposition="outside")
fig_total_txs.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

# --- مرتب‌سازی بر اساس حجم تراکنش ---
total_vol_sorted = total_summary.sort_values(by="volume", ascending=False)
fig_total_vol = px.bar(
    total_vol_sorted,
    x="platform",
    y="volume",
    text="volume",
    color="platform",
    title="Total Volume per Platform"
)
fig_total_vol.update_traces(textposition="outside")
fig_total_vol.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

col5, col6 = st.columns(2)
col5.plotly_chart(fig_total_txs, use_container_width=True)
col6.plotly_chart(fig_total_vol, use_container_width=True)
