import streamlit as st
import pandas as pd
import requests
import snowflake.connector
import plotly.graph_objects as go
import plotly.express as px
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# --- Page Config: Tab Title & Icon -------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Axelar : Interchain Transactions Overview",
    page_icon="https://img.cryptorank.io/coins/axelar1663924228506.png",
    layout="wide"
)
# --- Sidebar Footer Slightly Left-Aligned ------------------------------------------------------------------------------
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

# --- Title & Info Messages ---------------------------------------------------------------------------------------------
st.title("👥Users Activity")

st.info("📊 Charts initially display data for a default time range. Select a custom range to view results for your desired period.")
st.info("⏳ On-chain data retrieval may take a few moments. Please wait while the results load.")

# --- Snowflake Connection ----------------------------------------------------------------------------------------
snowflake_secrets = st.secrets["snowflake"]
user = snowflake_secrets["user"]
account = snowflake_secrets["account"]
private_key_str = snowflake_secrets["private_key"]
warehouse = snowflake_secrets.get("warehouse", "")
database = snowflake_secrets.get("database", "")
schema = snowflake_secrets.get("schema", "")

private_key_pem = f"-----BEGIN PRIVATE KEY-----\n{private_key_str}\n-----END PRIVATE KEY-----".encode("utf-8")
private_key = serialization.load_pem_private_key(
    private_key_pem,
    password=None,
    backend=default_backend()
)
private_key_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

conn = snowflake.connector.connect(
    user=user,
    account=account,
    private_key=private_key_bytes,
    warehouse=warehouse,
    database=database,
    schema=schema
)

# --- Time Frame & Period Selection --------------------------------------------------------------------------------------
timeframe = st.selectbox("Select Time Frame", ["month", "week", "day"])
start_date = st.date_input("Start Date", value=pd.to_datetime("2023-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("2025-07-31"))

# --- Build SQL Query ---------------------------------------------------------------------------------------------
date_trunc_level = timeframe.upper()  # Converts to MONTH, WEEK, or DAY

query = f"""
WITH table1 AS (
    WITH axelar_service AS (
        SELECT created_at, recipient_address AS user
        FROM axelar.axelscan.fact_transfers
        WHERE status = 'executed' AND simplified_status = 'received'
        UNION ALL
        SELECT created_at, data:call.transaction.from::STRING AS user
        FROM axelar.axelscan.fact_gmp 
        WHERE status = 'executed' AND simplified_status = 'received'
    )
    SELECT date_trunc('{timeframe}', created_at) AS "Date", COUNT(DISTINCT user) AS "Active Users"
    FROM axelar_service
    WHERE created_at::date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
),
table2 AS (
    WITH tab1 AS (
        WITH axelar_service AS (
            SELECT created_at, recipient_address AS user
            FROM axelar.axelscan.fact_transfers
            WHERE status = 'executed' AND simplified_status = 'received'
            UNION ALL
            SELECT created_at, data:call.transaction.from::STRING AS user
            FROM axelar.axelscan.fact_gmp 
            WHERE status = 'executed' AND simplified_status = 'received'
        )
        SELECT user, MIN(created_at::date) AS first_date
        FROM axelar_service
        GROUP BY 1
    )
    SELECT date_trunc('{timeframe}', first_date) AS "Date", COUNT(DISTINCT user) AS "New Users"
    FROM tab1
    WHERE first_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
)
SELECT 
    table1."Date" AS "Date",
    "Active Users", 
    COALESCE("New Users", 0) AS "Number of New Users",
    ROUND(AVG("Active Users") OVER (ORDER BY table1."Date")) AS "Avg Active Users Over Time",
    IFF("Active Users" > LAG("Active Users") OVER (ORDER BY table1."Date"), '🟢', 
        IFF("Active Users" = LAG("Active Users") OVER (ORDER BY table1."Date"), '⚪', '🔴')) AS "Change",
    (("Active Users" - LAG("Active Users") OVER (ORDER BY table1."Date")) / NULLIF(LAG("Active Users") OVER (ORDER BY table1."Date"), 0)) * 100 AS "Daily Change Active Users",
    SUM("Number of New Users") OVER (ORDER BY table1."Date") AS "Cumulative Users",
    ROUND(AVG("Number of New Users") OVER (ORDER BY table1."Date" ROWS BETWEEN 7 PRECEDING AND CURRENT ROW)) AS "Average 7 New Users",
    ROUND(AVG("Number of New Users") OVER (ORDER BY table1."Date" ROWS BETWEEN 30 PRECEDING AND CURRENT ROW)) AS "Average 30 New Users",
    "Active Users" - "Number of New Users" AS "Number of Recurring Users",
    ROUND(100 * "Number of New Users" / NULLIF("Active Users", 0), 2) AS "New Users Percentage",
    ROUND(100 * ("Active Users" - "Number of New Users") / NULLIF("Active Users", 0), 2) AS "Recurring Users Percentage",
    ROUND(AVG("Active Users") OVER (ORDER BY table1."Date" ROWS BETWEEN 7 PRECEDING AND CURRENT ROW)) AS "Average 7 Active Users",
    ROUND(AVG("Active Users") OVER (ORDER BY table1."Date" ROWS BETWEEN 30 PRECEDING AND CURRENT ROW)) AS "Average 30 Active Users"
FROM table1
LEFT JOIN table2 ON table1."Date" = table2."Date"
ORDER BY 1 ASC
"""

# --- Run Query & Load Data ------------------------------------------------------------------------------------------
df = pd.read_sql(query, conn)
df["Date"] = pd.to_datetime(df["Date"])

# --- KPI ------------------------------------------------------------------------------------------------------------
latest_date = df["Date"].max().date()
latest_cumulative = int(df["Cumulative Users"].iloc[-1])

st.metric(label="👥 Total Number of Axelar Users", value=f"{latest_cumulative:,}", help=f"Up to {latest_date}")

# --- Chart: Active Users vs Daily Change --------------------------------------------------------------------------
fig1 = go.Figure()
fig1.add_bar(x=df["Date"], y=df["Active Users"], name="Active Users")
fig1.add_trace(go.Scatter(x=df["Date"], y=df["Daily Change Active Users"], mode='lines+markers', name="Change %", yaxis="y2"))

fig1.update_layout(
    title="Axelar: Active Users Over Time (Change %)",
    yaxis=dict(title="Address count"),
    yaxis2=dict(title="Change (%)", overlaying="y", side="right"),
    xaxis=dict(title="Date"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig1, use_container_width=True)

# --- Row of Two Charts -------------------------------------------------------------------------------------------
col1, col2 = st.columns(2)

# Chart 1: New Users + Cumulative
with col1:
    fig2 = go.Figure()
    fig2.add_bar(x=df["Date"], y=df["Number of New Users"], name="New Users")
    fig2.add_trace(go.Scatter(x=df["Date"], y=df["Cumulative Users"], mode='lines+markers', name="Cumulative Users", yaxis="y2"))
    fig2.update_layout(
        title="Number of New Users Over Time",
        yaxis=dict(title="Address count"),
        yaxis2=dict(title="Address count", overlaying="y", side="right"),
        xaxis=dict(title="Date")
    )
    st.plotly_chart(fig2, use_container_width=True)

# Chart 2: Daily Avg Users
with col2:
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df["Date"], y=df["Avg Active Users Over Time"], mode='lines', name="All-Time Avg"))
    fig3.add_trace(go.Scatter(x=df["Date"], y=df["Average 7 Active Users"], mode='lines', name="7-Day Avg"))
    fig3.add_trace(go.Scatter(x=df["Date"], y=df["Average 30 Active Users"], mode='lines', name="30-Day Avg"))
    fig3.update_layout(
        title="Axelar: Dailily Average Users",
        yaxis=dict(title="Address count"),
        xaxis=dict(title="Date")
    )
    st.plotly_chart(fig3, use_container_width=True)

# --- Row of Two More Charts -------------------------------------------------------------------------------------
col3, col4 = st.columns(2)

# Chart 3: New vs Recurring Users
with col3:
    fig4 = go.Figure()
    fig4.add_bar(x=df["Date"], y=df["Number of New Users"], name="New Users")
    fig4.add_bar(x=df["Date"], y=df["Number of Recurring Users"], name="Recurring Users")
    fig4.update_layout(
        barmode="stack",
        title="New vs Recurring Users Over Time",
        xaxis_title="Date",
        yaxis_title="Address count"
    )
    st.plotly_chart(fig4, use_container_width=True)

# Chart 4: Normalized % Chart
with col4:
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(x=df["Date"], y=df["New Users Percentage"], stackgroup="one", name="New Users %"))
    fig5.add_trace(go.Scatter(x=df["Date"], y=df["Recurring Users Percentage"], stackgroup="one", name="Recurring Users %"))
    fig5.update_layout(
        title="New and Recurring Users Over Time (%Normalized)",
        xaxis_title="Date",
        yaxis_title="Percentage",
        yaxis=dict(ticksuffix="%")
    )
    st.plotly_chart(fig5, use_container_width=True)

# --- Final Table --------------------------------------------------------------------------------------------------
st.subheader("📋 Axelar: Users Stats")
st.dataframe(df)

# -------------------------------------------------------------------------------------------------------------------
# ---  MAU vs DAU ---------------------------------------------------------------------------------------------
query_stickiness = f"""
WITH DAU_u AS (
    WITH axelar_service AS (
        SELECT created_at, recipient_address AS user
        FROM axelar.axelscan.fact_transfers
        WHERE status = 'executed' AND simplified_status = 'received'
        UNION ALL
        SELECT created_at, data:call.transaction.from::STRING AS user
        FROM axelar.axelscan.fact_gmp 
        WHERE status = 'executed' AND simplified_status = 'received'
    )
    SELECT date_trunc('day', created_at) AS day, COUNT(DISTINCT user) AS DAU
    FROM axelar_service
    WHERE created_at::date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
),
MAU_u AS (
    WITH axelar_service AS (
        SELECT created_at, recipient_address AS user
        FROM axelar.axelscan.fact_transfers
        WHERE status = 'executed' AND simplified_status = 'received'
        UNION ALL
        SELECT created_at, data:call.transaction.from::STRING AS user
        FROM axelar.axelscan.fact_gmp 
        WHERE status = 'executed' AND simplified_status = 'received'
    )
    SELECT date_trunc('MONTH', created_at) AS month, COUNT(DISTINCT user) AS MAU
    FROM axelar_service
    WHERE created_at::date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1
),
mDAU AS (
    SELECT date_trunc('month', day) AS month, ROUND(AVG(DAU)) AS "Average DAU"
    FROM DAU_u
    GROUP BY 1
)
SELECT 
    a.month AS "Date", 
    MAU, 
    "Average DAU", 
    ROUND(((100 * "Average DAU") / MAU), 2) AS "Stickiness Ratio"
FROM mDAU a
LEFT JOIN MAU_u b USING (month)
ORDER BY 1 ASC
"""

df_stickiness = pd.read_sql(query_stickiness, conn)
df_stickiness["Date"] = pd.to_datetime(df_stickiness["Date"])

# --- نمودارها: MAU + Avg DAU و Stickiness Ratio --------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    fig_mau_dau = go.Figure()
    fig_mau_dau.add_bar(x=df_stickiness["Date"], y=df_stickiness["MAU"], name="MAU")
    fig_mau_dau.add_trace(go.Scatter(
        x=df_stickiness["Date"],
        y=df_stickiness["Average DAU"],
        mode="lines+markers",
        name="Avg. DAU",
        yaxis="y2"
    ))

    fig_mau_dau.update_layout(
        title="Axelar: MAU vs Avg. DAU",
        xaxis_title="Date",
        yaxis=dict(title="Address count"),
        yaxis2=dict(title="Address count", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.1, x=1, xanchor='right'),
    )
    st.plotly_chart(fig_mau_dau, use_container_width=True)

with col2:
    fig_stickiness = px.scatter(
        df_stickiness,
        x="Date",
        y="Stickiness Ratio",
        size="Stickiness Ratio",
        color="Stickiness Ratio",
        title="Axelar: Stickiness Ration Over Time"
    )
    fig_stickiness.update_traces(mode='markers+lines')
    fig_stickiness.update_layout(
        yaxis_title="Stickiness Ratio (%)",
        xaxis_title="Date",
    )
    st.plotly_chart(fig_stickiness, use_container_width=True)


