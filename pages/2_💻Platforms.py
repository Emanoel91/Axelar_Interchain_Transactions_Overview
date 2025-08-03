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

# --- Donut Charts: Share of Total ---
st.subheader("🍩 Share of Total TXs & Volume")

total_txs_share = df_filtered.groupby("platform")["num_txs"].sum().reset_index()
total_vol_share = df_filtered.groupby("platform")["volume"].sum().reset_index()

col5, col6 = st.columns(2)

fig_donut_txs = px.pie(total_txs_share, values="num_txs", names="platform",
                       title="Share of Transactions", hole=0.5)
fig_donut_vol = px.pie(total_vol_share, values="volume", names="platform",
                       title="Share of Volume", hole=0.5)

col5.plotly_chart(fig_donut_txs, use_container_width=True)
col6.plotly_chart(fig_donut_vol, use_container_width=True)
