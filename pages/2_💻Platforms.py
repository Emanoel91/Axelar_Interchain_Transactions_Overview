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

# --- API Data Fetch & Visualizations -----------------------------------------------------------------------------------
st.subheader("📡 Interchain Transfers by Platform (from Dune API)")

# Dune API call
API_URL = "https://api.dune.com/api/v1/query/5575605/results?api_key=kmCBMTxWKBxn6CVgCXhwDvcFL1fBp6rO"
response = requests.get(API_URL)
data = response.json()["result"]["rows"]
df_api = pd.DataFrame(data)

# Data cleaning
df_api["day"] = pd.to_datetime(df_api["day"])
df_api["num_txs"] = pd.to_numeric(df_api["num_txs"])
df_api["volume"] = pd.to_numeric(df_api["volume"])

# Time period filtering
df_api = df_api[(df_api["day"] >= pd.to_datetime(start_date)) & (df_api["day"] <= pd.to_datetime(end_date))]

# Time frame resampling
if timeframe != "day":
    df_api["day"] = df_api["day"].dt.to_period(timeframe).dt.to_timestamp()
    df_api = df_api.groupby(["day", "platform"], as_index=False)[["num_txs", "volume"]].sum()

# --- Row 1: Stacked Bar Charts: Transfers & Volume --------------------------------------------------------------------
st.markdown("### 🧱 Daily Number & Volume of Transfers by Platform")

col1, col2 = st.columns(2)
with col1:
    fig1 = px.bar(df_api, x="day", y="num_txs", color="platform", title="Number of Transfers", barmode="stack")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.bar(df_api, x="day", y="volume", color="platform", title="Transfer Volume", barmode="stack")
    st.plotly_chart(fig2, use_container_width=True)

# --- Row 2: Cumulative Line Charts -------------------------------------------------------------------------------------
st.markdown("### 📈 Cumulative Volume & Transfers by Platform")
df_api["cum_volume"] = df_api.groupby("platform")["volume"].cumsum()
df_api["cum_txs"] = df_api.groupby("platform")["num_txs"].cumsum()

col3, col4 = st.columns(2)
with col3:
    fig3 = px.line(df_api, x="day", y="cum_volume", color="platform", title="Cumulative Volume")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    fig4 = px.line(df_api, x="day", y="cum_txs", color="platform", title="Cumulative Transactions")
    st.plotly_chart(fig4, use_container_width=True)

# --- Row 3: Total Volume & Transfers by Platform -----------------------------------------------------------------------
st.markdown("### 📊 Total Volume & Transfers by Platform")
agg = df_api.groupby("platform", as_index=False).agg({
    "num_txs": "sum",
    "volume": "sum"
}).sort_values(by="num_txs", ascending=False)

col5, col6 = st.columns(2)
with col5:
    fig5 = px.bar(agg, x="platform", y="num_txs", text="num_txs", color="platform",
                  title="Total Number of Transfers")
    fig5.update_traces(textposition='outside')
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    fig6 = px.bar(agg, x="platform", y="volume", text="volume", color="platform",
                  title="Total Transfer Volume")
    fig6.update_traces(textposition='outside')
    st.plotly_chart(fig6, use_container_width=True)

