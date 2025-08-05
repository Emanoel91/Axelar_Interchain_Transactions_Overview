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

st.info("🔔To view the most recent updates, click on the '...' in the top-right corner of the page and select 'Rerun'.")

# --- Snowflake Connection ----------------------------------------------------------------------------------------------
conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse="SNOWFLAKE_LEARNING_WH",
    database="AXELAR",
    schema="PUBLIC"
)

# -------------------------------------------------------------------------------------------------------------------------
# --- Platform & API Mapping --------------------------------------------------------------------------------------------
platform_apis = {
    "Interchain Token Service": [
        "https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0xB5FB4BE02232B1bBA4dC8f81dc24C26980dE9e3C",
        "https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=axelar1aqcj54lzz0rk22gvqgcn8fr5tx4rzwdv5wv5j9dmnacgefvd7wzsy2j2mr"
    ],
    "Squid": [
        "https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0xce16F69375520ab01377ce7B88f5BA8C48F8D666",
        "https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0xdf4fFDa22270c12d0b5b3788F1669D709476111E",
        "https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8"
    ],
    "MintDAO Bridge": [
        "https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0xD0FFD6fE14b2037897Ad8cD072F6d6DE30CF8e56"
    ],
    "Prime Protocol": [
        "https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0xbe54BaFC56B468d4D20D609F0Cf17fFc56b99913"
    ],
    "The Junkyard": [
        "https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0x66423a1b45e14EaB8B132665FebC7Ec86BfcBF44"
    ],
    "Nya Bridge": [
        "https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0xcbBA104B6CB4960a70E5dfc48E76C536A1f19609"
    ],
    "eesee.io": [
        "https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0xEac19c899098951fc6d0e6a7832b090474E2C292"
    ]
}

# -------------------------------------------------------------------------------------------------------------------------
# --- Platform Selection (Top of Page) ---------------------------------------------------------------------------------
st.markdown("### 🔍 Select a Platform or Service to Explore")
selected_platform = st.selectbox(
    "Choose a platform to load data for:",
    options=list(platform_apis.keys()),
    index=0
)

st.info("Select a platform above to load its cross-chain transaction data.")

# -------------------------------------------------------------------------------------------------------------------------
# --- Load and Normalize Data for Selected Platform --------------------------------------------------------------------
@st.cache_data
def load_platform_data(api_urls):
    records = []
    for url in api_urls:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "source_chains" in data:
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
    return pd.DataFrame(records)

df_transfers = load_platform_data(platform_apis[selected_platform])


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

df_table = df_transfers[["Path", "Volume of Transfers (USD)", "Number of Transfers"]].sort_values(
    by="Volume of Transfers (USD)", ascending=False).reset_index(drop=True)
df_table.index += 1  

st.dataframe(df_table, use_container_width=True)

# --- Horizontal Bar Chart ------------------------------------------------------------------------
# --- Top N Selection ------------------------------------------------------------------------------------------
st.subheader("📊 Top Transfer Paths")

top_n = st.selectbox("Select number of top paths to display:", [5, 10, 15, 20], index=1)  # پیش‌فرض 10

# انتخاب N مسیر برتر بر اساس تعداد تراکنش و حجم تراکنش
top_by_txs = df_transfers.sort_values("Number of Transfers", ascending=False).head(top_n)
top_by_volume = df_transfers.sort_values("Volume of Transfers (USD)", ascending=False).head(top_n)

# ایجاد دو ستون کنار هم
col1, col2 = st.columns(2)

with col1:
    fig_txs = px.bar(
        top_by_txs.sort_values("Number of Transfers"),  # برای داشتن ترتیب از پایین به بالا
        x="Number of Transfers",
        y="Path",
        orientation='h',
        title=f"Top {top_n} Paths by Number of Transfers",
        labels={"Number of Transfers": "Number of Transfers", "Path": "Transfer Path"}
    )
    fig_txs.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_txs, use_container_width=True)

with col2:
    fig_vol = px.bar(
        top_by_volume.sort_values("Volume of Transfers (USD)"),  # برای داشتن ترتیب مناسب
        x="Volume of Transfers (USD)",
        y="Path",
        orientation='h',
        title=f"Top {top_n} Paths by Volume (USD)",
        labels={"Volume of Transfers (USD)": "Volume (USD)", "Path": "Transfer Path"}
    )
    fig_vol.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_vol, use_container_width=True)

# --- Heatmaps --------------------------------------------------------------------------
# --- Heatmap Filters ---------------------------------------------------------------------------------------------------
st.subheader("🎛️ Heatmap Filters")

all_sources = sorted(df_transfers["Source Chain"].unique())
all_destinations = sorted(df_transfers["Destination Chain"].unique())

selected_sources = st.multiselect("Select Source Chains", options=all_sources, default=all_sources)
selected_destinations = st.multiselect("Select Destination Chains", options=all_destinations, default=all_destinations)

# فیلتر کردن داده‌ها بر اساس انتخاب کاربر
filtered_df = df_transfers[
    df_transfers["Source Chain"].isin(selected_sources) &
    df_transfers["Destination Chain"].isin(selected_destinations)
]

# --- Heatmap: Volume by Source & Destination --------------------------------------------------------------------------
st.subheader("🔥 Heatmap of Transfer Volume (USD)")
pivot_vol = filtered_df.pivot_table(
    index="Destination Chain",
    columns="Source Chain",
    values="Volume of Transfers (USD)",
    aggfunc="sum",
    fill_value=0
)
fig_heatmap_vol = px.imshow(
    pivot_vol,
    text_auto=True,
    aspect="auto",
    color_continuous_scale='Viridis',
    title="Transfer Volume Heatmap (Filtered)"
)
st.plotly_chart(fig_heatmap_vol, use_container_width=True)

# --- Heatmap: Number of Transfers by Source & Destination -------------------------------------------------------------
st.subheader("📈 Heatmap of Number of Transfers")
pivot_txs = filtered_df.pivot_table(
    index="Destination Chain",
    columns="Source Chain",
    values="Number of Transfers",
    aggfunc="sum",
    fill_value=0
)
fig_heatmap_txs = px.imshow(
    pivot_txs,
    text_auto=True,
    aspect="auto",
    color_continuous_scale='Cividis',
    title="Transfer Count Heatmap (Filtered)"
)
st.plotly_chart(fig_heatmap_txs, use_container_width=True)

