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
st.title("💎Routes & Tokens")

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

# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
# --- Extract and Flatten Nested API Structure -------------------------------------------------------------------------
@st.cache_data
def load_and_flatten_api_data():
    urls = [
        "https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0xB5FB4BE02232B1bBA4dC8f81dc24C26980dE9e3C",
        "https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=axelar1aqcj54lzz0rk22gvqgcn8fr5tx4rzwdv5wv5j9dmnacgefvd7wzsy2j2mr"
    ]

    records = []
    for url in urls:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for source_entry in data["source_chains"]:
                source_chain = source_entry["key"]
                for dest in source_entry.get("destination_chains", []):
                    dest_chain = dest["key"]
                    volume = dest["volume"]
                    num_txs = dest["num_txs"]
                    records.append({
                        "Source Chain": source_chain,
                        "Destination Chain": dest_chain,
                        "Volume of Transfers (USD)": volume,
                        "Number of Transfers": num_txs,
                        "Path": f"{source_chain} ➡ {dest_chain}"
                    })

    df = pd.DataFrame(records)
    return df

df_transfers = load_and_flatten_api_data()

# --- KPIs -------------------------------------------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🔗 Unique Source Chains", df_transfers["Source Chain"].nunique())
with col2:
    st.metric("🎯 Unique Destination Chains", df_transfers["Destination Chain"].nunique())
with col3:
    st.metric("🧭 Unique Paths", df_transfers["Path"].nunique())

# --- Display Transfer Table -------------------------------------------------------------------------------------------
st.subheader("📋 Transfer Details Table")

# مرتب‌سازی جدول و ریست ایندکس از 1
df_table = df_transfers[["Path", "Volume of Transfers (USD)", "Number of Transfers"]].sort_values(
    by="Volume of Transfers (USD)", ascending=False).reset_index(drop=True)
df_table.index += 1  # شماره‌گذاری از 1

st.dataframe(df_table, use_container_width=True)

# --- Horizontal Bar Chart: Number of Transfers ------------------------------------------------------------------------
st.subheader("📦 Transfers per Path (Number)")
fig_txs = px.bar(
    df_transfers.sort_values("Number of Transfers", ascending=True),
    x="Number of Transfers",
    y="Path",
    orientation='h',
    title="Number of Transfers per Path"
)
st.plotly_chart(fig_txs, use_container_width=True)

# --- Horizontal Bar Chart: Volume of Transfers ------------------------------------------------------------------------
st.subheader("💰 Transfers per Path (Volume in USD)")
fig_vol = px.bar(
    df_transfers.sort_values("Volume of Transfers (USD)", ascending=True),
    x="Volume of Transfers (USD)",
    y="Path",
    orientation='h',
    title="Volume of Transfers per Path"
)
st.plotly_chart(fig_vol, use_container_width=True)


# --- Heatmap: Volume by Source & Destination --------------------------------------------------------------------------
st.subheader("🔥 Heatmap of Transfer Volume (USD)")
pivot_vol = df_transfers.pivot_table(index="Destination Chain", columns="Source Chain", values="Volume of Transfers (USD)", aggfunc="sum", fill_value=0)
fig_heatmap_vol = px.imshow(pivot_vol, text_auto=True, aspect="auto", color_continuous_scale='Viridis', title="Transfer Volume Heatmap")
st.plotly_chart(fig_heatmap_vol, use_container_width=True)

# --- Heatmap: Number of Transfers by Source & Destination -------------------------------------------------------------
st.subheader("📈 Heatmap of Number of Transfers")
pivot_txs = df_transfers.pivot_table(index="Destination Chain", columns="Source Chain", values="Number of Transfers", aggfunc="sum", fill_value=0)
fig_heatmap_txs = px.imshow(pivot_txs, text_auto=True, aspect="auto", color_continuous_scale='Cividis', title="Transfer Count Heatmap")
st.plotly_chart(fig_heatmap_txs, use_container_width=True)

