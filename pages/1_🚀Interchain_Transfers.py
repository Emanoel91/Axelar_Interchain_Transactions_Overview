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

# --- Title with Logo ---------------------------------------------------------------------------------------------------
st.title("🚀Interchain Transfers")

st.info("📊Charts initially display data for a default time range. Select a custom range to view results for your desired period.")
st.info("⏳On-chain data retrieval may take a few moments. Please wait while the results load.")

# --- Snowflake Connection --------------------------------------------------------------------------------------------------
conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse="SNOWFLAKE_LEARNING_WH",
    database="AXELAR",
    schema="PUBLIC"
)

# --- Time Frame & Period Selection ---
timeframe = st.selectbox("Select Time Frame", ["month", "week", "day"])
start_date = st.date_input("Start Date", value=pd.to_datetime("2023-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("2025-07-31"))

# --- Query Functions ---------------------------------------------------------------------------------------
# --- Getting D.API ---
@st.cache_data(ttl=3600)  # --- cache for 1 hour
def load_dune_tvl():
    url = "https://api.dune.com/api/v1/query/5524904/results?api_key=kmCBMTxWKBxn6CVgCXhwDvcFL1fBp6rO"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["result"]["rows"])
        if "TVL" in df.columns:
            df["TVL"] = pd.to_numeric(df["TVL"], errors="coerce")
            df = df.sort_values("TVL", ascending=False)
        return df
    else:
        st.error(f"Failed to fetch Dune data: {response.status_code}")
        return pd.DataFrame(columns=["Chain", "Token Symbol", "TVL"])

# ----------------------
@st.cache_data
def load_main_data(timeframe, start_date, end_date):
    query = f"""
    SELECT date_trunc('{timeframe}', block_timestamp) AS "Date",
           COUNT(DISTINCT tx_id) AS "TXs Count",
           tx_succeeded AS "TX Success"
    FROM AXELAR.CORE.FACT_TRANSACTIONS
    WHERE block_timestamp::date >= '{start_date}'
      AND block_timestamp::date <= '{end_date}'
    GROUP BY 1, 3
    ORDER BY 1
    """
    return pd.read_sql(query, conn)

# --- Load Data ----------------------------------------------------------------------------------------
dune_tvl = load_dune_tvl()
df = load_main_data(timeframe, start_date, end_date)
# ------------------------------------------------------------------------------------------------------
if not dune_tvl.empty:
    # --- chain search filter ---
    chain_list = dune_tvl["Chain"].unique().tolist()
    selected_chain = st.selectbox("🔎 Choose your desired chain", chain_list, index=chain_list.index("Axelar") if "Axelar" in chain_list else 0)

    # --- TVL for selected chain ---
    selected_tvl = dune_tvl.loc[dune_tvl["Chain"] == selected_chain, "TVL"].sum()
    st.metric(label=f"TVL of {selected_chain}", value=f"${selected_tvl:,.0f}")

    # --- table ---
    st.markdown("<h4 style='font-size:18px;'>TVL of Different Chains</h4>", unsafe_allow_html=True)
    st.dataframe(dune_tvl.style.format({"TVL": "{:,.0f}"}), use_container_width=True)

    # --- chart ---
    def human_format(num):
        if num >= 1e9:
            return f"{num/1e9:.1f}B"
        elif num >= 1e6:
            return f"{num/1e6:.1f}M"
        elif num >= 1e3:
            return f"{num/1e3:.1f}K"
        else:
            return str(int(num))

    fig = px.bar(
        dune_tvl.head(15),
        x="Chain",
        y="TVL",
        color="Chain",
        title="Top Chains by TVL ($USD)",
        text=dune_tvl.head(15)["TVL"].apply(human_format)
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(xaxis_title="Chain", yaxis_title="TVL", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data available.")

# --- Row 2: Bar Chart ---
fig_bar = px.bar(df, x="Date", y="TXs Count", color="TX Success",
                 title="Number of Transactions Based on Success Over Time")
st.plotly_chart(fig_bar)
