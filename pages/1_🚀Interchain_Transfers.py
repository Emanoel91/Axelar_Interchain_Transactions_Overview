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
st.title("🚀Interchain Transfers")

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
    title="Transactions by Service Over Time",
)
fig_txs_norm = px.bar(
    txs_grouped, x="timeframe", y="num_txs", color="service",
    title="Normalized Transactions by Service Over Time",
    barmode="relative"
)
fig_txs_norm.update_layout(barmode="stack", barnorm="percent")

col1, col2 = st.columns(2)
col1.plotly_chart(fig_txs, use_container_width=True)
col2.plotly_chart(fig_txs_norm, use_container_width=True)

# --- Row 3: Volume Over Time ---

volume_grouped = service_df.groupby(["timeframe", "service"])["volume"].sum().reset_index()

fig_vol = px.bar(
    volume_grouped, x="timeframe", y="volume", color="service",
    title="Volume by Service Over Time",
)
fig_vol_norm = px.bar(
    volume_grouped, x="timeframe", y="volume", color="service",
    title="Normalized Volume by Service Over Time",
    barmode="relative"
)
fig_vol_norm.update_layout(barmode="stack", barnorm="percent")

col1, col2 = st.columns(2)
col1.plotly_chart(fig_vol, use_container_width=True)
col2.plotly_chart(fig_vol_norm, use_container_width=True)

# --- Row 4: Donut Charts ---

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

# --- Row: Top Source Chains by Transfer Count ----------------------------------------------------------------------------------------------------------------
st.subheader("📤 Source Chains by Number of Transfers")

@st.cache_data(ttl=3600)
def load_top_source_chains(start_date, end_date):
    query = f"""
    WITH axelar_services AS (
        SELECT created_at,
               LOWER(data:send:original_source_chain) AS source_chain,
               id
        FROM axelar.axelscan.fact_transfers
        WHERE created_at::date >= '{start_date}'
          AND created_at::date <= '{end_date}'
          AND status = 'executed'
          AND simplified_status = 'received'

        UNION ALL

        SELECT created_at,
               TO_VARCHAR(LOWER(data:call:chain)) AS source_chain,
               TO_VARCHAR(id) AS id
        FROM axelar.axelscan.fact_gmp
        WHERE created_at::date >= '{start_date}'
          AND created_at::date <= '{end_date}'
          AND status = 'executed'
          AND simplified_status = 'received'
    )

    SELECT 
        source_chain AS "Source Chain",
        COUNT(DISTINCT id) AS "Transfer Count"
    FROM axelar_services
    GROUP BY 1
    ORDER BY 2 DESC
    """
    return pd.read_sql(query, conn)

# --- Load data ---
top_chains_df = load_top_source_chains(start_date, end_date)

if not top_chains_df.empty:
    # --- Reset index to start from 1 ---
    top_chains_df = top_chains_df.reset_index(drop=True)
    top_chains_df.index += 1  # Start index from 1

    # --- Display Table ---
    col1, col2 = st.columns([0.5, 0.5])

    with col1:
        # -- st.markdown("**Top Source Chains Table**")
        st.dataframe(top_chains_df, use_container_width=True)

    # --- Bar Chart for Top 10 Chains ---
    top10_df = top_chains_df.head(10)

    fig_barh = px.bar(
        top10_df.sort_values("Transfer Count"),  # sort ascending for horizontal layout
        x="Transfer Count",
        y="Source Chain",
        orientation='h',
        color="Source Chain",
        text="Transfer Count",
        title="🏆Top 10 Source Chains by Transfers Count"
    )
    fig_barh.update_traces(textposition='outside')
    fig_barh.update_layout(showlegend=False)

    with col2:
        st.plotly_chart(fig_barh, use_container_width=True)
else:
    st.warning("No source chain data found for the selected period.")

# --- Row: Active Users Over Time ------------------------------------------------------------------------------------------------------------------------
st.subheader("👥 Active Users and Averages Over Time")

@st.cache_data(ttl=3600)
def load_active_users(timeframe, start_date, end_date):
    query = f"""
    WITH axelar_services AS (
        SELECT created_at,
               sender_address AS user
        FROM axelar.axelscan.fact_transfers
        WHERE created_at::date >= '{start_date}'
          AND created_at::date <= '{end_date}'
          AND status = 'executed'
          AND simplified_status = 'received'

        UNION ALL

        SELECT created_at,
               TO_VARCHAR(data:call:transaction:from) AS user
        FROM axelar.axelscan.fact_gmp
        WHERE created_at::date >= '{start_date}'
          AND created_at::date <= '{end_date}'
          AND status = 'executed'
          AND simplified_status = 'received'
    )

    SELECT 
        DATE_TRUNC('{timeframe}', created_at) AS "Date",
        COUNT(DISTINCT user) AS "AU",
        ROUND(AVG(COUNT(DISTINCT user)) OVER (ORDER BY DATE_TRUNC('{timeframe}', created_at) ROWS BETWEEN 7 PRECEDING AND CURRENT ROW)) AS "Average 7 AU",
        ROUND(AVG(COUNT(DISTINCT user)) OVER (ORDER BY DATE_TRUNC('{timeframe}', created_at) ROWS BETWEEN 30 PRECEDING AND CURRENT ROW)) AS "Average 30 AU"
    FROM axelar_services
    GROUP BY 1
    ORDER BY 1
    """
    return pd.read_sql(query, conn)

# --- Load Data ---
df_au = load_active_users(timeframe, start_date, end_date)

if not df_au.empty:
    fig_au = px.line(
        df_au,
        x="Date",
        y=["AU", "Average 7 AU", "Average 30 AU"],
        title="D/W/MAU and Average 7/30 D/W/MAU",
        markers=True
    )
    fig_au.update_layout(
        yaxis_title="Active Users",
        legend_title="Metric",
        hovermode="x unified"
    )
    st.plotly_chart(fig_au, use_container_width=True)
else:
    st.warning("No active user data found for selected period.")


# --- Row: User KPIs ---------------------------------------------------------------------------------------------------------------------------------
# --- Row: User KPIs (Timeframe-aware) ---
st.subheader("📌 User Summary KPIs")

@st.cache_data(ttl=3600)
def load_user_kpis_with_timeframe(timeframe, start_date, end_date):
    query = f"""
    WITH table1 AS (
        WITH axelar_services AS (
            SELECT created_at,
                   sender_address AS user
            FROM axelar.axelscan.fact_transfers
            WHERE created_at::date >= '{start_date}'
              AND created_at::date <= '{end_date}'
              AND status = 'executed'
              AND simplified_status = 'received'

            UNION ALL

            SELECT created_at,
                   TO_VARCHAR(data:call:transaction:from) AS user
            FROM axelar.axelscan.fact_gmp
            WHERE created_at::date >= '{start_date}'
              AND created_at::date <= '{end_date}'
              AND status = 'executed'
              AND simplified_status = 'received'
        )

        SELECT 
            DATE_TRUNC('{timeframe}', created_at) AS "Date",
            COUNT(DISTINCT user) AS "AU",
            ROUND(AVG(COUNT(DISTINCT user)) OVER (
                ORDER BY DATE_TRUNC('{timeframe}', created_at) 
                ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
            )) AS "Average 7 AU",
            ROUND(AVG(COUNT(DISTINCT user)) OVER (
                ORDER BY DATE_TRUNC('{timeframe}', created_at) 
                ROWS BETWEEN 30 PRECEDING AND CURRENT ROW
            )) AS "Average 30 AU"
        FROM axelar_services
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT 1
    ),

    table2 AS (
        WITH axelar_services AS (
            SELECT created_at,
                   sender_address AS user
            FROM axelar.axelscan.fact_transfers
            WHERE created_at::date >= '{start_date}'
              AND created_at::date <= '{end_date}'
              AND status = 'executed'
              AND simplified_status = 'received'

            UNION ALL

            SELECT created_at,
                   TO_VARCHAR(data:call:transaction:from) AS user
            FROM axelar.axelscan.fact_gmp
            WHERE created_at::date >= '{start_date}'
              AND created_at::date <= '{end_date}'
              AND status = 'executed'
              AND simplified_status = 'received'
        )

        SELECT 
            COUNT(DISTINCT user) AS "Total Users"
        FROM axelar_services
    )

    SELECT "Total Users", "Average 7 AU", "Average 30 AU"
    FROM table1, table2
    """
    return pd.read_sql(query, conn)

# --- Load and Display KPIs ---
user_kpis = load_user_kpis_with_timeframe(timeframe, start_date, end_date)

if not user_kpis.empty:
    total_users = int(user_kpis.loc[0, "Total Users"])
    avg7 = int(user_kpis.loc[0, "Average 7 AU"])
    avg30 = int(user_kpis.loc[0, "Average 30 AU"])

    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Total Users", f"{total_users:,}", help="Number of unique users during selected period")
    col2.metric(f"📅 Avg. 7 {timeframe.capitalize()} AU", f"{avg7:,}", help="7-period rolling average of active users")
    col3.metric(f"📆 Avg. 30 {timeframe.capitalize()} AU", f"{avg30:,}", help="30-period rolling average of active users")
else:
    st.warning("No user KPI data found for selected time range.")
