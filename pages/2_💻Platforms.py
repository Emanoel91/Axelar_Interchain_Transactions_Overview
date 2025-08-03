import streamlit as st
import pandas as pd
import requests
import snowflake.connector
import plotly.express as px

# --- Page Config ---
st.set_page_config(
    page_title="Axelar : Interchain Transactions Overview",
    page_icon="https://img.cryptorank.io/coins/axelar1663924228506.png",
    layout="wide"
)

# --- Title & Info ---
st.title("🚀Axelar : Interchain Transactions Overview")
st.info("📊 Charts initially display data for a default time range. Select a custom range to view results for your desired period.")
st.info("⏳ On-chain data retrieval may take a few moments. Please wait while the results load.")

# --- Snowflake Connection ---
conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse="SNOWFLAKE_LEARNING_WH",
    database="AXELAR",
    schema="PUBLIC"
)

# --- Time Frame & Period Selection ---
timeframe = st.selectbox("Select Time Frame", ["day", "week", "month"])
start_date = pd.to_datetime(st.date_input("Start Date", value=pd.to_datetime("2023-01-01")))
end_date = pd.to_datetime(st.date_input("End Date", value=pd.to_datetime("2025-07-31")))

# --- Fetch API Data ---
api_url = "https://api.dune.com/api/v1/query/5575605/results?api_key=kmCBMTxWKBxn6CVgCXhwDvcFL1fBp6rO"
response = requests.get(api_url)
data_json = response.json()

if "result" in data_json and "rows" in data_json["result"]:
    df_api = pd.DataFrame(data_json["result"]["rows"])
    df_api["day"] = pd.to_datetime(df_api["day"])
    
    # Apply date filter
    df_api = df_api[(df_api["day"] >= start_date) & (df_api["day"] <= end_date)]

    # Resample based on timeframe
    if timeframe != "day":
        df_api["day"] = df_api["day"].dt.to_period(timeframe[0].upper()).dt.to_timestamp()

    # Aggregate by timeframe + platform
    df_grouped = df_api.groupby(["day", "platform"]).agg(
        num_txs=("num_txs", "sum"),
        volume=("volume", "sum")
    ).reset_index()

    # Cumulative values
    df_cum = df_grouped.copy()
    df_cum["cum_volume"] = df_cum.groupby("platform")["volume"].cumsum()
    df_cum["cum_txs"] = df_cum.groupby("platform")["num_txs"].cumsum()

    # Total per platform
    df_total = df_grouped.groupby("platform").agg(
        num_txs=("num_txs", "sum"),
        volume=("volume", "sum")
    ).reset_index()

    # --- Row 1: Stacked Bar Charts ---
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.bar(df_grouped, x="day", y="num_txs", color="platform",
                      title="📦 Number of Transfers per Platform Over Time")
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        fig2 = px.bar(df_grouped, x="day", y="volume", color="platform",
                      title="💰 Volume of Transfers per Platform Over Time")
        st.plotly_chart(fig2, use_container_width=True)

    # --- Row 2: Cumulative Line Charts ---
    col3, col4 = st.columns(2)
    with col3:
        fig3 = px.line(df_cum, x="day", y="cum_volume", color="platform",
                       title="📈 Cumulative Volume Over Time")
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        fig4 = px.line(df_cum, x="day", y="cum_txs", color="platform",
                       title="📈 Cumulative Transfers Over Time")
        st.plotly_chart(fig4, use_container_width=True)

    # --- Row 3: Total Bar Charts per Platform ---
    col5, col6 = st.columns(2)
    with col5:
        fig5 = px.bar(df_total, x="num_txs", y="platform", orientation="h", color="platform", text="num_txs",
                      title="🔢 Total Transfers per Platform")
        fig5.update_traces(textposition="outside")
        st.plotly_chart(fig5, use_container_width=True)
    with col6:
        fig6 = px.bar(df_total, x="volume", y="platform", orientation="h", color="platform", text="volume",
                      title="💸 Total Volume per Platform")
        fig6.update_traces(textposition="outside")
        st.plotly_chart(fig6, use_container_width=True)

else:
    st.error("Failed to load data from API.")
