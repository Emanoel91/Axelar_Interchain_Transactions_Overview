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
import streamlit as st
import pandas as pd

# --- Function to load data with a given query and apply date filter ---
@st.cache_data(ttl=3600)
def load_token_transfer_stats(start_date, end_date):
    query = f"""
    WITH axelar_service AS (
      SELECT 
        created_at, 
        LOWER(data:send:original_source_chain) AS source_chain, 
        LOWER(data:send:original_destination_chain) AS destination_chain,
        sender_address AS user, 

        CASE 
          WHEN IS_ARRAY(data:send:amount) THEN NULL
          WHEN IS_OBJECT(data:send:amount) THEN NULL
          WHEN TRY_TO_DOUBLE(data:send:amount::STRING) IS NOT NULL THEN TRY_TO_DOUBLE(data:send:amount::STRING)
          ELSE NULL
        END AS amount,

        CASE 
          WHEN IS_ARRAY(data:send:amount) OR IS_ARRAY(data:link:price) THEN NULL
          WHEN IS_OBJECT(data:send:amount) OR IS_OBJECT(data:link:price) THEN NULL
          WHEN TRY_TO_DOUBLE(data:send:amount::STRING) IS NOT NULL AND TRY_TO_DOUBLE(data:link:price::STRING) IS NOT NULL 
            THEN TRY_TO_DOUBLE(data:send:amount::STRING) * TRY_TO_DOUBLE(data:link:price::STRING)
          ELSE NULL
        END AS amount_usd,

        CASE 
          WHEN IS_ARRAY(data:send:fee_value) THEN NULL
          WHEN IS_OBJECT(data:send:fee_value) THEN NULL
          WHEN TRY_TO_DOUBLE(data:send:fee_value::STRING) IS NOT NULL THEN TRY_TO_DOUBLE(data:send:fee_value::STRING)
          ELSE NULL
        END AS fee,

        id,  
        'Token Transfers' AS service, 
        data:link:asset::STRING AS raw_asset

      FROM axelar.axelscan.fact_transfers
      WHERE status = 'executed'
        AND simplified_status = 'received'
        AND created_at::date>='{start_date}' AND created_at::date<='{end_date}'

      UNION ALL

      SELECT  
        created_at,
        data:call.chain::STRING AS source_chain,
        data:call.returnValues.destinationChain::STRING AS destination_chain,
        data:call.transaction.from::STRING AS user,

        CASE 
          WHEN IS_ARRAY(data:amount) OR IS_OBJECT(data:amount) THEN NULL
          WHEN TRY_TO_DOUBLE(data:amount::STRING) IS NOT NULL THEN TRY_TO_DOUBLE(data:amount::STRING)
          ELSE NULL
        END AS amount,

        CASE 
          WHEN IS_ARRAY(data:value) OR IS_OBJECT(data:value) THEN NULL
          WHEN TRY_TO_DOUBLE(data:value::STRING) IS NOT NULL THEN TRY_TO_DOUBLE(data:value::STRING)
          ELSE NULL
        END AS amount_usd,

        COALESCE(
          CASE 
            WHEN IS_ARRAY(data:gas:gas_used_amount) OR IS_OBJECT(data:gas:gas_used_amount) 
              OR IS_ARRAY(data:gas_price_rate:source_token.token_price.usd) OR IS_OBJECT(data:gas_price_rate:source_token.token_price.usd) 
            THEN NULL
            WHEN TRY_TO_DOUBLE(data:gas:gas_used_amount::STRING) IS NOT NULL 
              AND TRY_TO_DOUBLE(data:gas_price_rate:source_token.token_price.usd::STRING) IS NOT NULL 
            THEN TRY_TO_DOUBLE(data:gas:gas_used_amount::STRING) * TRY_TO_DOUBLE(data:gas_price_rate:source_token.token_price.usd::STRING)
            ELSE NULL
          END,
          CASE 
            WHEN IS_ARRAY(data:fees:express_fee_usd) OR IS_OBJECT(data:fees:express_fee_usd) THEN NULL
            WHEN TRY_TO_DOUBLE(data:fees:express_fee_usd::STRING) IS NOT NULL THEN TRY_TO_DOUBLE(data:fees:express_fee_usd::STRING)
            ELSE NULL
          END
        ) AS fee,

        id, 
        'GMP' AS service, 
        data:symbol::STRING AS raw_asset

      FROM axelar.axelscan.fact_gmp 
      WHERE status = 'executed'
        AND simplified_status = 'received'
        AND created_at::date>='{start_date}' AND created_at::date<='{end_date}'
    )

    SELECT 
      CASE 
        WHEN raw_asset='arb-wei' THEN 'ARB'
        WHEN raw_asset='avalanche-uusdc' THEN 'Avalanche USDC'
        WHEN raw_asset='avax-wei' THEN 'AVAX'
        WHEN raw_asset='bnb-wei' THEN 'BNB'
        WHEN raw_asset='busd-wei' THEN 'BUSD'
        WHEN raw_asset='cbeth-wei' THEN 'cbETH'
        WHEN raw_asset='cusd-wei' THEN 'cUSD'
        WHEN raw_asset='dai-wei' THEN 'DAI'
        WHEN raw_asset='dot-planck' THEN 'DOT'
        WHEN raw_asset='eeur' THEN 'EURC'
        WHEN raw_asset='ern-wei' THEN 'ERN'
        WHEN raw_asset='eth-wei' THEN 'ETH'
        WHEN raw_asset ILIKE 'factory/sei10hub%' THEN 'SEILOR'
        WHEN raw_asset='fil-wei' THEN 'FIL'
        WHEN raw_asset='frax-wei' THEN 'FRAX'
        WHEN raw_asset='ftm-wei' THEN 'FTM'
        WHEN raw_asset='glmr-wei' THEN 'GLMR'
        WHEN raw_asset='hzn-wei' THEN 'HZN'
        WHEN raw_asset='link-wei' THEN 'LINK'
        WHEN raw_asset='matic-wei' THEN 'MATIC'
        WHEN raw_asset='mkr-wei' THEN 'MKR'
        WHEN raw_asset='mpx-wei' THEN 'MPX'
        WHEN raw_asset='oath-wei' THEN 'OATH'
        WHEN raw_asset='op-wei' THEN 'OP'
        WHEN raw_asset='orbs-wei' THEN 'ORBS'
        WHEN raw_asset='factory/sei10hud5e5er4aul2l7sp2u9qp2lag5u4xf8mvyx38cnjvqhlgsrcls5qn5ke/seilor' THEN 'SEILOR'
        WHEN raw_asset='pepe-wei' THEN 'PEPE'
        WHEN raw_asset='polygon-uusdc' THEN 'Polygon USDC'
        WHEN raw_asset='reth-wei' THEN 'rETH'
        WHEN raw_asset='ring-wei' THEN 'RING'
        WHEN raw_asset='shib-wei' THEN 'SHIB'
        WHEN raw_asset='sonne-wei' THEN 'SONNE'
        WHEN raw_asset='stuatom' THEN 'stATOM'
        WHEN raw_asset='uatom' THEN 'ATOM'
        WHEN raw_asset='uaxl' THEN 'AXL'
        WHEN raw_asset='ukuji' THEN 'KUJI'
        WHEN raw_asset='ulava' THEN 'LAVA'
        WHEN raw_asset='uluna' THEN 'LUNA'
        WHEN raw_asset='ungm' THEN 'NGM'
        WHEN raw_asset='uni-wei' THEN 'UNI'
        WHEN raw_asset='uosmo' THEN 'OSMO'
        WHEN raw_asset='usomm' THEN 'SOMM'
        WHEN raw_asset='ustrd' THEN 'STRD'
        WHEN raw_asset='utia' THEN 'TIA'
        WHEN raw_asset='uumee' THEN 'UMEE'
        WHEN raw_asset='uusd' THEN 'USTC'
        WHEN raw_asset='uusdc' THEN 'USDC'
        WHEN raw_asset='uusdt' THEN 'USDT'
        WHEN raw_asset='vela-wei' THEN 'VELA'
        WHEN raw_asset='wavax-wei' THEN 'WAVAX'
        WHEN raw_asset='wbnb-wei' THEN 'WBNB'
        WHEN raw_asset='wbtc-satoshi' THEN 'WBTC'
        WHEN raw_asset='weth-wei' THEN 'WETH'
        WHEN raw_asset='wfil-wei' THEN 'WFIL'
        WHEN raw_asset='wftm-wei' THEN 'WFTM'
        WHEN raw_asset='wglmr-wei' THEN 'WGLMR'
        WHEN raw_asset='wmai-wei' THEN 'WMAI'
        WHEN raw_asset='wmatic-wei' THEN 'WMATIC'
        WHEN raw_asset='wsteth-wei' THEN 'wstETH'
        WHEN raw_asset='yield-eth-wei' THEN 'yieldETH' 
        ELSE raw_asset 
      END AS "symbol",
      service as "service", 
      COUNT(DISTINCT id) AS "Transfers Count",
      COUNT(DISTINCT user) AS "Users Count", 
      ROUND(SUM(amount_usd)) AS "Transfers Volume (USD)",
      ROUND(SUM(amount)) AS "Transfers Volume",
      ROUND(SUM(fee)) AS "Transfer Fees (USD)",
      ROUND(AVG(fee), 3) AS "Avg Transfer Fee (USD)",
      COUNT(DISTINCT (source_chain || '➡' || destination_chain)) AS "Number of Paths"
    FROM axelar_service
    WHERE raw_asset IS NOT NULL
    GROUP BY 1, 2
    ORDER BY 3 DESC
    """

    return pd.read_sql(query, conn)

# --- Load data using selected date ---
df_token_stats = load_token_transfer_stats(start_date, end_date)

if not df_token_stats.empty:
    # تنظیم ایندکس از 1 شروع شود
    df_token_stats.index = range(1, len(df_token_stats) + 1)

    # Formatting numbers with thousands separator
    for col in ["Transfers Count", "Users Count", "Transfers Volume (USD)", "Transfers Volume", "Transfer Fees (USD)", "Number of Paths"]:
        df_token_stats[col] = df_token_stats[col].apply(lambda x: f"{x:,}")

    df_token_stats["Avg Transfer Fee (USD)"] = df_token_stats["Avg Transfer Fee (USD)"].map("{:,.3f}".format)

    def highlight_rows(row):
        color = ''
        if row["SERVICE"] == "GMP":
            color = '#f8b88c'
        elif row["SERVICE"] == "Token Transfers":
            color = '#7cd5fd'
        return [f'background-color: {color}' for _ in row]

    st.subheader("Token transfer statistics using Axelar cross-chain services")
    st.dataframe(df_token_stats.style.apply(highlight_rows, axis=1), use_container_width=True)

else:
    st.warning("No data found for the selected period.")
# --------------------------------------------------------------------------------------------------------------------------------

emoji_index = ['🥇', '🥈', '🥉', '🏅', '🎖']

def get_top5_table(df, metric, service_type):
    df_filtered = df[df["service"] == service_type]
    df_sorted = df_filtered.sort_values(by=metric, ascending=False).head(5).copy()
    df_sorted.reset_index(drop=True, inplace=True)
    df_sorted.index = emoji_index[:len(df_sorted)]
    return df_sorted[["symbol", metric]]

# ---  tables for GMP ---
st.subheader("🏆 Top 5 Tokens via **GMP Service**")

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### 📦 By Transfers Count")
    st.dataframe(get_top5_table(df_token_stats, "Transfers Count", "GMP"), use_container_width=True)

    st.markdown("#### 👥 By Users Count")
    st.dataframe(get_top5_table(df_token_stats, "Users Count", "GMP"), use_container_width=True)

with col2:
    st.markdown("#### 💰 By Transfer Volume (USD)")
    st.dataframe(get_top5_table(df_token_stats, "Transfers Volume (USD)", "GMP"), use_container_width=True)

    st.markdown("#### 🧾 By Transfer Fees (USD)")
    st.dataframe(get_top5_table(df_token_stats, "Transfer Fees (USD)", "GMP"), use_container_width=True)

# --- tables for Token Transfers ---
st.subheader("🏆 Top 5 Tokens via **Token Transfers Service**")

col3, col4 = st.columns(2)
with col3:
    st.markdown("#### 📦 By Transfers Count")
    st.dataframe(get_top5_table(df_token_stats, "Transfers Count", "Token Transfers"), use_container_width=True)

    st.markdown("#### 👥 By Users Count")
    st.dataframe(get_top5_table(df_token_stats, "Users Count", "Token Transfers"), use_container_width=True)

with col4:
    st.markdown("#### 💰 By Transfer Volume (USD)")
    st.dataframe(get_top5_table(df_token_stats, "Transfers Volume (USD)", "Token Transfers"), use_container_width=True)

    st.markdown("#### 🧾 By Transfer Fees (USD)")
    st.dataframe(get_top5_table(df_token_stats, "Transfer Fees (USD)", "Token Transfers"), use_container_width=True)
