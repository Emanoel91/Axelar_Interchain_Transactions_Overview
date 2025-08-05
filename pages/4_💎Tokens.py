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
st.title("💎Tokens")

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

# -----------------------------------------------------------------------------------------------------------------------
# --- Row: Transfers by Source Chain over Time ---
st.subheader("🔄 Transfers Count by Source Chain Over Time")

@st.cache_data(ttl=3600)
def load_chain_transfers(timeframe, start_date, end_date):
    query = f"""
    WITH axelar_services AS (
        SELECT created_at,
               LOWER(data:send:original_source_chain) AS source_chain,
               LOWER(data:send:original_destination_chain) AS destination_chain,
               sender_address AS user,
               data:send:amount * data:link:price AS amount,
               data:send:fee_value AS fee,
               id,
               'Token Transfers' AS service
        FROM axelar.axelscan.fact_transfers
        WHERE created_at::date >= '{start_date}'
          AND created_at::date <= '{end_date}'
          AND status = 'executed'
          AND simplified_status = 'received'

        UNION ALL

        SELECT created_at,
               TO_VARCHAR(LOWER(data:call:chain)) AS source_chain,
               TO_VARCHAR(LOWER(data:call:returnValues:destinationChain)) AS destination_chain,
               TO_VARCHAR(data:call:transaction:from) AS user,
               data:value AS amount,
               COALESCE(
                   ((data:gas:gas_used_amount) * (data:gas_price_rate:source_token.token_price.usd)),
                   TRY_CAST(data:fees:express_fee_usd::float AS FLOAT)
               ) AS fee,
               TO_VARCHAR(id) AS id,
               'GMP' AS service
        FROM axelar.axelscan.fact_gmp
        WHERE created_at::date >= '{start_date}'
          AND created_at::date <= '{end_date}'
          AND status = 'executed'
          AND simplified_status = 'received'
    )

    SELECT DATE_TRUNC('{timeframe}', created_at) AS "Date",
           source_chain AS "Source Chain",
           COUNT(DISTINCT id) AS "Transfer Count",
           SUM(COUNT(DISTINCT id)) OVER (PARTITION BY source_chain ORDER BY DATE_TRUNC('{timeframe}', created_at)) AS "Total Transfers Count"
    FROM axelar_services
    GROUP BY 1, 2
    ORDER BY 1
    """
    return pd.read_sql(query, conn)

# --- Load and Check ----------------------------------------------------
df_transfers = load_chain_transfers(timeframe, start_date, end_date)

if not df_transfers.empty:
    # --- Chart 1: Transfer Count per Source Chain over Time (Stacked Bar) ---
    fig_stack_bar = px.bar(
        df_transfers,
        x="Date",
        y="Transfer Count",
        color="Source Chain",
        title="Transfers Count by Source Chain",
    )

    # --- Chart 2: Cumulative Transfers per Source Chain (Line) ---
    fig_line = px.line(
        df_transfers,
        x="Date",
        y="Total Transfers Count",
        color="Source Chain",
        title="Cumulative Transfers Count by Source Chain",
    )

    col1, col2 = st.columns(2)
    col1.plotly_chart(fig_stack_bar, use_container_width=True)
    col2.plotly_chart(fig_line, use_container_width=True)
else:
    st.warning("No transfer data found for selected period.")

