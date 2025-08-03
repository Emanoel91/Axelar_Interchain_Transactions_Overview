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
st.title("🚀Axelar : Interchain Transactions Overview")

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

# --- Load Axelar Service Volume & TXs from Dune API ---
@st.cache_data(ttl=3600)
def load_service_data():
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
        st.error(f"Failed to fetch service data: {response.status_code}")
        return pd.DataFrame(columns=["day", "volume", "num_txs", "service"])

# --- Load and Filter Service Data ---
service_df_raw = load_service_data()
service_df = service_df_raw[
    (service_df_raw["day"].dt.date >= start_date) &
    (service_df_raw["day"].dt.date <= end_date)
].copy()
service_df["timeframe"] = service_df["day"].dt.to_period(timeframe[0].upper()).dt.to_timestamp()

# --- Row 1: Summary Metrics ---
st.subheader("📦 Total Transfer Stats by Service")

col1, col2, col3, col4 = st.columns(4)

gmp_tx_count = service_df.loc[service_df["service"] == "GMP", "num_txs"].sum()
token_tx_count = service_df.loc[service_df["service"] == "Token Transfers", "num_txs"].sum()
gmp_volume = service_df.loc[service_df["service"] == "GMP", "volume"].sum()
token_volume = service_df.loc[service_df["service"] == "Token Transfers", "volume"].sum()

col1.metric("GMP Transactions", f"{gmp_tx_count:,.0f}")
col2.metric("Token Transfers Transactions", f"{token_tx_count:,.0f}")
col3.metric("GMP Volume ($)", f"${gmp_volume:,.0f}")
col4.metric("Token Transfers Volume ($)", f"${token_volume:,.0f}")

# --- Row 2: TX Count Over Time ---
st.subheader("📈 Transactions Over Time by Service")

txs_grouped = service_df.groupby(["timeframe", "service"])["num_txs"].sum().reset_index()

fig_txs = px.bar(
    txs_grouped, x="timeframe", y="num_txs", color="service",
    title="Transactions by Service (Stacked)",
)
fig_txs_norm = px.bar(
    txs_grouped, x="timeframe", y="num_txs", color="service",
    title="Normalized Transactions by Service",
    barmode="relative"
)
fig_txs_norm.update_layout(barmode="stack", barnorm="percent")

col1, col2 = st.columns(2)
col1.plotly_chart(fig_txs, use_container_width=True)
col2.plotly_chart(fig_txs_norm, use_container_width=True)

# --- Row 3: Volume Over Time ---
st.subheader("💰 Volume Over Time by Service")

volume_grouped = service_df.groupby(["timeframe", "service"])["volume"].sum().reset_index()

fig_vol = px.bar(
    volume_grouped, x="timeframe", y="volume", color="service",
    title="Volume by Service (Stacked)",
)
fig_vol_norm = px.bar(
    volume_grouped, x="timeframe", y="volume", color="service",
    title="Normalized Volume by Service",
    barmode="relative"
)
fig_vol_norm.update_layout(barmode="stack", barnorm="percent")

col1, col2 = st.columns(2)
col1.plotly_chart(fig_vol, use_container_width=True)
col2.plotly_chart(fig_vol_norm, use_container_width=True)

# --- Row 4: Donut Charts ---
st.subheader("🥧 Service Share Distribution")

total_txs_share = service_df.groupby("service")["num_txs"].sum().reset_index()
total_vol_share = service_df.groupby("service")["volume"].sum().reset_index()

fig_donut_txs = px.pie(
    total_txs_share, values="num_txs", names="service",
    title="Share of Total Transactions by Service", hole=0.5
)

fig_donut_vol = px.pie(
    total_vol_share, values="volume", names="service",
    title="Share of Total Volume by Service", hole=0.5
)

col1, col2 = st.columns(2)
col1.plotly_chart(fig_donut_txs, use_container_width=True)
col2.plotly_chart(fig_donut_vol, use_container_width=True)
