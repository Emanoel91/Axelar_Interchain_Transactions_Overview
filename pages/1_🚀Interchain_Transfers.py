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

# --- Fetch Data from API --------------------------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_data():
    url = "https://api.axelarscan.io/api/interchainChart"
    response = requests.get(url)
    json_data = response.json()
    df = pd.DataFrame(json_data['data'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

df = load_data()

# --- Filter by date range ------------------------------------------------------------------------------------------
df = df[(df['timestamp'] >= pd.to_datetime(start_date)) & (df['timestamp'] <= pd.to_datetime(end_date))]

# --- Resample data based on timeframe ------------------------------------------------------------------------------
if timeframe == "week":
    df['period'] = df['timestamp'].dt.to_period('W').apply(lambda r: r.start_time)
elif timeframe == "month":
    df['period'] = df['timestamp'].dt.to_period('M').apply(lambda r: r.start_time)
else:
    df['period'] = df['timestamp']

grouped = df.groupby('period').agg({
    'gmp_num_txs': 'sum',
    'gmp_volume': 'sum',
    'transfers_num_txs': 'sum',
    'transfers_volume': 'sum'
}).reset_index()

grouped['total_txs'] = grouped['gmp_num_txs'] + grouped['transfers_num_txs']
grouped['total_volume'] = grouped['gmp_volume'] + grouped['transfers_volume']

# --- KPI Section ---------------------------------------------------------------------------------------------------
st.markdown("## 📦 Total Transfer Stats by Service")
col1, col2, col3, col4 = st.columns(4)
col1.metric("🔁 Total GMP Transactions", f"{grouped['gmp_num_txs'].sum():,}")
col2.metric("🔄 Total Token Transfers Transactions", f"{grouped['transfers_num_txs'].sum():,}")
col3.metric("💰 Total GMP Volume ($)", f"${grouped['gmp_volume'].sum():,.0f}")
col4.metric("💸 Total Token Transfers Volume ($)", f"${grouped['transfers_volume'].sum():,.0f}")

# --- Row 2: Transactions Over Time ----------------------------------------------------------------------------------
import streamlit as st
import plotly.graph_objects as go

st.markdown("## 📈 Transactions Over Time by Service")

# -- Stacked bar + line
fig1 = go.Figure()
fig1.add_trace(go.Bar(x=grouped['period'], y=grouped['gmp_num_txs'], name='GMP', marker_color='#ff7400'))
fig1.add_trace(go.Bar(x=grouped['period'], y=grouped['transfers_num_txs'], name='Token Transfers', marker_color='#00a1f7'))
fig1.add_trace(go.Scatter(x=grouped['period'], y=grouped['total_txs'], name='Total', mode='lines+markers', marker_color='black'))
fig1.update_layout(barmode='stack', title="Transactions By Service Over Time")

# -- Normalized stacked bar
df_norm_tx = grouped.copy()
df_norm_tx['gmp_norm'] = df_norm_tx['gmp_num_txs'] / df_norm_tx['total_txs']
df_norm_tx['transfers_norm'] = df_norm_tx['transfers_num_txs'] / df_norm_tx['total_txs']

fig2 = go.Figure()
fig2.add_trace(go.Bar(x=df_norm_tx['period'], y=df_norm_tx['gmp_norm'], name='GMP', marker_color='#ff7400'))
fig2.add_trace(go.Bar(x=df_norm_tx['period'], y=df_norm_tx['transfers_norm'], name='Token Transfers', marker_color='#00a1f7'))
fig2.update_layout(barmode='stack', title="Normalized Transactions By Service Over Time", yaxis_tickformat='%')

col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.plotly_chart(fig2, use_container_width=True)


# --- Row 3: Volume Over Time ----------------------------------------------------------------------------------------
st.markdown("## 💵 Volume Over Time by Service")

# -- Stacked bar + line
fig3 = go.Figure()
fig3.add_trace(go.Bar(x=grouped['period'], y=grouped['gmp_volume'], name='GMP', marker_color='#ff7400'))
fig3.add_trace(go.Bar(x=grouped['period'], y=grouped['transfers_volume'], name='Token Transfers', marker_color='#00a1f7'))
fig3.add_trace(go.Scatter(x=grouped['period'], y=grouped['total_volume'], name='Total', mode='lines+markers', marker_color='black'))
fig3.update_layout(barmode='stack', title="Volume By Service Over Time")

# -- Normalized Charts
df_norm_vol = grouped.copy()
df_norm_vol['gmp_norm'] = df_norm_vol['gmp_volume'] / df_norm_vol['total_volume']
df_norm_vol['transfers_norm'] = df_norm_vol['transfers_volume'] / df_norm_vol['total_volume']

fig4 = go.Figure()
fig4.add_trace(go.Bar(x=df_norm_vol['period'], y=df_norm_vol['gmp_norm'], name='GMP', marker_color='#ff7400'))
fig4.add_trace(go.Bar(x=df_norm_vol['period'], y=df_norm_vol['transfers_norm'], name='Token Transfers', marker_color='#00a1f7'))
fig4.update_layout(barmode='stack', title="Normalized Volume By Service Over Time", yaxis_tickformat='%')

col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    st.plotly_chart(fig4, use_container_width=True)

# --- Row 4: Donut Charts ---------------------------------------------------------------------------------------------
total_gmp_tx = grouped['gmp_num_txs'].sum()
total_transfers_tx = grouped['transfers_num_txs'].sum()

total_gmp_vol = grouped['gmp_volume'].sum()
total_transfers_vol = grouped['transfers_volume'].sum()

tx_df = pd.DataFrame({
    "Service": ["GMP", "Token Transfers"],
    "Count": [total_gmp_tx, total_transfers_tx]
})

donut_tx = px.pie(
    tx_df,
    names="Service",
    values="Count",
    color="Service",  
    hole=0.5,
    title="Share of Total Transactions By Service",
    color_discrete_map={
        "GMP": "#ff7400",
        "Token Transfers": "#00a1f7"
    }
)

vol_df = pd.DataFrame({
    "Service": ["GMP", "Token Transfers"],
    "Volume": [total_gmp_vol, total_transfers_vol]
})

donut_vol = px.pie(
    vol_df,
    names="Service",
    values="Volume",
    color="Service",  
    hole=0.5,
    title="Share of Total Volume By Service",
    color_discrete_map={
        "GMP": "#ff7400",
        "Token Transfers": "#00a1f7"
    }
)

col5, col6 = st.columns(2)
col5.plotly_chart(donut_tx, use_container_width=True)
col6.plotly_chart(donut_vol, use_container_width=True)


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


# --- Sidebar Footer Slightly Left-Aligned ---
st.sidebar.markdown(
    """
    <style>
    .sidebar-footer {
        position: fixed;
        bottom: 20px;
        width: 250px;
        font-size: 13px;
        color: gray;
        margin-left: 5px; # -- MOVE LEFT
        text-align: left;  
    }
    .sidebar-footer img {
        width: 16px;
        height: 16px;
        vertical-align: middle;
        border-radius: 50%;
        margin-right: 5px;
    }
    .sidebar-footer a {
        color: gray;
        text-decoration: none;
    }
    </style>

    <div class="sidebar-footer">
        <div>
            <a href="https://x.com/axelar" target="_blank">
                <img src="https://img.cryptorank.io/coins/axelar1663924228506.png" alt="Axelar Logo">
                Powered by Axelar
            </a>
        </div>
        <div style="margin-top: 5px;">
            <a href="https://x.com/0xeman_raz" target="_blank">
                <img src="https://pbs.twimg.com/profile_images/1841479747332608000/bindDGZQ_400x400.jpg" alt="Eman Raz">
                Built by Eman Raz
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
