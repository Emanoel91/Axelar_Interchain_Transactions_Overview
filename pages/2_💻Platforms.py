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

# --- API Fetch and DataFrame Preparation ------------------------------------------------------------------------------  
api_url = "https://api.dune.com/api/v1/query/5575605/results?api_key=kmCBMTxWKBxn6CVgCXhwDvcFL1fBp6rO"
response = requests.get(api_url)

if response.status_code == 200:
    data = response.json()
    df_api = pd.DataFrame(data["result"]["rows"])

    if "day" in df_api.columns:
        # تبدیل ستون day به datetime و حذف ردیف‌های نامعتبر
        df_api["day"] = pd.to_datetime(df_api["day"], errors="coerce")
        df_api = df_api.dropna(subset=["day"])

        # تبدیل start_date و end_date به datetime (برای اطمینان)
        start_date_dt = pd.to_datetime(start_date)
        end_date_dt = pd.to_datetime(end_date)

        # فیلتر داده‌ها بر اساس بازه زمانی انتخاب شده
        df_api = df_api[(df_api["day"] >= start_date_dt) & (df_api["day"] <= end_date_dt)]

        # تعیین ستون time_bucket بر اساس بازه انتخابی
        df_api["time_bucket"] = df_api["day"]
        if timeframe == "week":
            df_api["time_bucket"] = df_api["day"].dt.to_period("W").apply(lambda r: r.start_time)
        elif timeframe == "month":
            df_api["time_bucket"] = df_api["day"].dt.to_period("M").apply(lambda r: r.start_time)

        # --- Row 1: Stacked Bar Charts --------------------------------------------------------------------------------
        st.subheader("📦 Transfers by Platform Over Time")

        col1, col2 = st.columns(2)

        with col1:
            fig_num = px.bar(
                df_api,
                x="time_bucket",
                y="num_txs",
                color="platform",
                title="Number of Transfers by Platform",
                labels={"time_bucket": "Date", "num_txs": "Transfers"}
            )
            st.plotly_chart(fig_num, use_container_width=True)

        with col2:
            fig_vol = px.bar(
                df_api,
                x="time_bucket",
                y="volume",
                color="platform",
                title="Volume of Transfers by Platform",
                labels={"time_bucket": "Date", "volume": "Volume (USD)"}
            )
            st.plotly_chart(fig_vol, use_container_width=True)

        # --- Row 2: Cumulative Line Charts ----------------------------------------------------------------------------
        st.subheader("📈 Cumulative Volume and Transfers")

        df_api_sorted = df_api.sort_values("day")
        df_api_sorted["cumulative_volume"] = df_api_sorted.groupby("platform")["volume"].cumsum()
        df_api_sorted["cumulative_txs"] = df_api_sorted.groupby("platform")["num_txs"].cumsum()

        col3, col4 = st.columns(2)

        with col3:
            fig_cum_vol = px.line(
                df_api_sorted,
                x="day",
                y="cumulative_volume",
                color="platform",
                title="Cumulative Volume Over Time"
            )
            st.plotly_chart(fig_cum_vol, use_container_width=True)

        with col4:
            fig_cum_txs = px.line(
                df_api_sorted,
                x="day",
                y="cumulative_txs",
                color="platform",
                title="Cumulative Transfers Over Time"
            )
            st.plotly_chart(fig_cum_txs, use_container_width=True)

        # --- Row 3: Total Transfers and Volume by Platform ------------------------------------------------------------
        st.subheader("📊 Total Transfers and Volume per Platform")

        summary = df_api.groupby("platform").agg(
            total_volume=pd.NamedAgg(column="volume", aggfunc="sum"),
            total_txs=pd.NamedAgg(column="num_txs", aggfunc="sum")
        ).reset_index()

        col5, col6 = st.columns(2)

        with col5:
            fig_bar_txs = px.bar(
                summary,
                x="platform",
                y="total_txs",
                text="total_txs",
                title="Total Transfers by Platform",
                color="platform"
            )
            fig_bar_txs.update_traces(textposition="outside")
            st.plotly_chart(fig_bar_txs, use_container_width=True)

        with col6:
            fig_bar_vol = px.bar(
                summary,
                x="platform",
                y="total_volume",
                text="total_volume",
                title="Total Volume by Platform",
                color="platform"
            )
            fig_bar_vol.update_traces(textposition="outside")
            st.plotly_chart(fig_bar_vol, use_container_width=True)

    else:
        st.error("❌ The API response does not include a 'day' column.")
else:
    st.error(f"❌ Failed to fetch data from API. Status code: {response.status_code}")
