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

# --- Load Axelar Platforms Transfer Data from Dune API ---
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
        st.error(f"Failed to fetch platform data: {response.status_code}")
        return pd.DataFrame(columns=["date", "volume", "num_txs", "platform"])

# --- Filter and Resample Platform Data ---
platform_df_raw = load_platform_data()

# Filter based on selected date
platform_df = platform_df_raw[
    (platform_df_raw["date"].dt.date >= start_date) &
    (platform_df_raw["date"].dt.date <= end_date)
].copy()

# Resample to selected timeframe
if timeframe == "day":
    platform_df["period"] = platform_df["date"]
elif timeframe == "week":
    platform_df["period"] = platform_df["date"].dt.to_period("W").dt.start_time
elif timeframe == "month":
    platform_df["period"] = platform_df["date"].dt.to_period("M").dt.start_time

# ====================
# Row 1: Stacked Bar Charts - Volume & TXs Over Time
# ====================
st.subheader("📊 Transfers Over Time (Grouped by Platform)")

grouped_time = platform_df.groupby(["period", "platform"]).agg({
    "volume": "sum",
    "num_txs": "sum"
}).reset_index()

col1, col2 = st.columns(2)

fig_txs_stacked = px.bar(
    grouped_time,
    x="period", y="num_txs", color="platform",
    title="📦 Number of Transfers Over Time",
)
fig_txs_stacked.update_layout(barmode="stack")

fig_volume_stacked = px.bar(
    grouped_time,
    x="period", y="volume", color="platform",
    title="💰 Volume of Transfers Over Time (USD)",
)
fig_volume_stacked.update_layout(barmode="stack")

col1.plotly_chart(fig_txs_stacked, use_container_width=True)
col2.plotly_chart(fig_volume_stacked, use_container_width=True)

# ====================
# Row 2: Cumulative Area Charts
# ====================
st.subheader("📈 Cumulative Transfers by Platform")

# Cumulative sum over time
cumulative_df = grouped_time.sort_values("period").copy()
cumulative_df["cum_volume"] = cumulative_df.groupby("platform")["volume"].cumsum()
cumulative_df["cum_num_txs"] = cumulative_df.groupby("platform")["num_txs"].cumsum()

col1, col2 = st.columns(2)

fig_cum_txs = px.area(
    cumulative_df, x="period", y="cum_num_txs", color="platform",
    title="🔁 Cumulative Transactions Over Time"
)

fig_cum_volume = px.area(
    cumulative_df, x="period", y="cum_volume", color="platform",
    title="💸 Cumulative Volume Over Time (USD)"
)

col1.plotly_chart(fig_cum_txs, use_container_width=True)
col2.plotly_chart(fig_cum_volume, use_container_width=True)

# ====================
# Row 3: Total Volume & TXs by Platform
# ====================
st.subheader("🏁 Total Transfers by Platform")

total_by_platform = platform_df.groupby("platform").agg({
    "volume": "sum",
    "num_txs": "sum"
}).reset_index()

# مرتب‌سازی
total_by_platform = total_by_platform.sort_values("num_txs", ascending=False)

col1, col2 = st.columns(2)

fig_bar_txs = px.bar(
    total_by_platform,
    x="platform", y="num_txs", color="platform", text="num_txs",
    title="📦 Total Transactions per Platform"
)
fig_bar_txs.update_traces(texttemplate='%{text:.2s}', textposition='outside')
fig_bar_txs.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

fig_bar_vol = px.bar(
    total_by_platform.sort_values("volume", ascending=False),
    x="platform", y="volume", color="platform", text="volume",
    title="💰 Total Volume per Platform (USD)"
)
fig_bar_vol.update_traces(texttemplate='%{text:.2s}', textposition='outside')
fig_bar_vol.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

col1.plotly_chart(fig_bar_txs, use_container_width=True)
col2.plotly_chart(fig_bar_vol, use_container_width=True)

