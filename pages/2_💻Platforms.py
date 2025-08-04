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
st.title("💻Platforms Powered By Axelar")

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
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

# --- Load Platform Transfer Data from Dune API -------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_platform_data():
    url = "https://api.dune.com/api/v1/query/5576048/results?api_key=kmCBMTxWKBxn6CVgCXhwDvcFL1fBp6rO"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["result"]["rows"])
        df["date"] = pd.to_datetime(df["date"])
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        df["num_txs"] = pd.to_numeric(df["num_txs"], errors="coerce")
        return df
    else:
        st.error(f"Failed to fetch platform data: {response.status_code}")
        return pd.DataFrame(columns=["date", "volume", "num_txs", "platform"])

platform_df_raw = load_platform_data()
platform_df = platform_df_raw[
    (platform_df_raw["date"].dt.date >= start_date) &
    (platform_df_raw["date"].dt.date <= end_date)
].copy()

# --- Row 2: Platform-wise Pie Charts ------------------------------------------------------------------------------------
st.subheader("🔄 Platform Share of Transfers and Volume")

pie_col1, pie_col2 = st.columns(2)

with pie_col1:
    txs_by_platform = platform_df.groupby("platform")["num_txs"].sum().reset_index()
    fig_txs = px.pie(txs_by_platform, names="platform", values="num_txs", title="Transactions by Platform")
    st.plotly_chart(fig_txs, use_container_width=True)

with pie_col2:
    volume_by_platform = platform_df.groupby("platform")["volume"].sum().reset_index()
    fig_volume = px.pie(volume_by_platform, names="platform", values="volume", title="Volume by Platform ($)")
    st.plotly_chart(fig_volume, use_container_width=True)

# --- Row 3: Time Series Stacked Bar Charts -----------------------------------------------------------------------------
st.subheader("📈 Time Series of Transfers and Volume by Platform")

# Convert to desired timeframe
platform_df["timeframe"] = platform_df["date"].dt.to_period(timeframe[0].upper()).dt.to_timestamp()

# Aggregate data
grouped_df = platform_df.groupby(["timeframe", "platform"]).agg({
    "num_txs": "sum",
    "volume": "sum"
}).reset_index()

# --- Chart 1: Stacked Bar for num_txs ---
bar_col1, bar_col2 = st.columns(2)

with bar_col1:
    fig_stack_txs = px.bar(
        grouped_df,
        x="timeframe",
        y="num_txs",
        color="platform",
        title="Transactions Over Time by Platform",
        labels={"num_txs": "Number of Transactions", "timeframe": "Time"}
    )
    fig_stack_txs.update_layout(barmode='stack', xaxis_title="Time", yaxis_title="Transactions")
    st.plotly_chart(fig_stack_txs, use_container_width=True)

# --- Chart 2: Stacked Bar for volume ---
with bar_col2:
    fig_stack_volume = px.bar(
        grouped_df,
        x="timeframe",
        y="volume",
        color="platform",
        title="Volume Over Time by Platform ($)",
        labels={"volume": "Volume ($)", "timeframe": "Time"}
    )
    fig_stack_volume.update_layout(barmode='stack', xaxis_title="Time", yaxis_title="Volume ($)")
    st.plotly_chart(fig_stack_volume, use_container_width=True)


# ------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------
# --- SQL Query: Overview with Time Filter (Row1) -------------------------------------------------------------------------------
query_overview = f"""
with overview as (with axelar_services as (
select data:send:amount * data:link:price as amount, recipient_address as user, 
id, 'Token Transfers' as service, case 
when sender_address ilike '%0xce16F69375520ab01377ce7B88f5BA8C48F8D666%' then 'Squid'
when sender_address ilike '%0xdf4fFDa22270c12d0b5b3788F1669D709476111E%' then 'Squid'
when sender_address ilike '%0xB5FB4BE02232B1bBA4dC8f81dc24C26980dE9e3C%' then 'Interchain Token Service'
when sender_address ilike '%0xD0FFD6fE14b2037897Ad8cD072F6d6DE30CF8e56%' then 'MintDAO Bridge'
when sender_address ilike '%0xbe54BaFC56B468d4D20D609F0Cf17fFc56b99913%' then 'Prime Protocol'
when sender_address ilike '%0x0ADFb7975aa7c3aD90c57AEa8FDe5E31a721E9bb%' then 'Rango Exchange'
when sender_address ilike '%0x66423a1b45e14EaB8B132665FebC7Ec86BfcBF44%' then 'The Junkyard'
when sender_address ilike '%axelar1aqcj54lzz0rk22gvqgcn8fr5tx4rzwdv5wv5j9dmnacgefvd7wzsy2j2mr%' then 'Interchain Token Service'
when sender_address ilike '%0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8%' then 'Squid'
when sender_address ilike '%0xcbBA104B6CB4960a70E5dfc48E76C536A1f19609%' then 'Nya Bridge'
when sender_address ilike '%0xEac19c899098951fc6d0e6a7832b090474E2C292%' then 'eesee.io'
end as "Platform"
from axelar.axelscan.fact_transfers
where (sender_address ilike '%0xce16F69375520ab01377ce7B88f5BA8C48F8D666%'
or sender_address ilike '%0xdf4fFDa22270c12d0b5b3788F1669D709476111E%'
or sender_address ilike '%0xB5FB4BE02232B1bBA4dC8f81dc24C26980dE9e3C%'
or sender_address ilike '%0xD0FFD6fE14b2037897Ad8cD072F6d6DE30CF8e56%'
or sender_address ilike '%0xbe54BaFC56B468d4D20D609F0Cf17fFc56b99913%'
or sender_address ilike '%0x0ADFb7975aa7c3aD90c57AEa8FDe5E31a721E9bb%'
or sender_address ilike '%0x66423a1b45e14EaB8B132665FebC7Ec86BfcBF44%'
or sender_address ilike '%axelar1aqcj54lzz0rk22gvqgcn8fr5tx4rzwdv5wv5j9dmnacgefvd7wzsy2j2mr%'
or sender_address ilike '%0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8%'
or sender_address ilike '%0xcbBA104B6CB4960a70E5dfc48E76C536A1f19609%'
or sender_address ilike '%0xEac19c899098951fc6d0e6a7832b090474E2C292%')
and status='executed'
and simplified_status='received'
and (created_at::date >= '{start_date}' and created_at::date <= '{end_date}')

union all

select data:value as amount, 
to_varchar(data:call:transaction:from) as user,
to_varchar(id) as id, 'GMP' as service, case 
when data:approved:returnValues:contractAddress ilike '%0xce16F69375520ab01377ce7B88f5BA8C48F8D666%' then 'Squid'
when data:approved:returnValues:contractAddress ilike '%0xdf4fFDa22270c12d0b5b3788F1669D709476111E%' then 'Squid'
when data:approved:returnValues:contractAddress ilike '%0xB5FB4BE02232B1bBA4dC8f81dc24C26980dE9e3C%' then 'Interchain Token Service'
when data:approved:returnValues:contractAddress ilike '%0xD0FFD6fE14b2037897Ad8cD072F6d6DE30CF8e56%' then 'MintDAO Bridge'
when data:approved:returnValues:contractAddress ilike '%0xbe54BaFC56B468d4D20D609F0Cf17fFc56b99913%' then 'Prime Protocol'
when data:approved:returnValues:contractAddress ilike '%0x0ADFb7975aa7c3aD90c57AEa8FDe5E31a721E9bb%' then 'Rango Exchange'
when data:approved:returnValues:contractAddress ilike '%0x66423a1b45e14EaB8B132665FebC7Ec86BfcBF44%' then 'The Junkyard'
when data:approved:returnValues:contractAddress ilike '%axelar1aqcj54lzz0rk22gvqgcn8fr5tx4rzwdv5wv5j9dmnacgefvd7wzsy2j2mr%' then 'Interchain Token Service'
when data:approved:returnValues:contractAddress ilike '%0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8%' then 'Squid'
when data:approved:returnValues:contractAddress ilike '%0xcbBA104B6CB4960a70E5dfc48E76C536A1f19609%' then 'Nya Bridge'
when data:approved:returnValues:contractAddress ilike '%0xEac19c899098951fc6d0e6a7832b090474E2C292%' then 'eesee.io'
end as "Platform"
from axelar.axelscan.fact_gmp
where (data:approved:returnValues:contractAddress ilike '%0xce16F69375520ab01377ce7B88f5BA8C48F8D666%'
or data:approved:returnValues:contractAddress ilike '%0xdf4fFDa22270c12d0b5b3788F1669D709476111E%'
or data:approved:returnValues:contractAddress ilike '%0xB5FB4BE02232B1bBA4dC8f81dc24C26980dE9e3C%'
or data:approved:returnValues:contractAddress ilike '%0xD0FFD6fE14b2037897Ad8cD072F6d6DE30CF8e56%'
or data:approved:returnValues:contractAddress ilike '%0xbe54BaFC56B468d4D20D609F0Cf17fFc56b99913%'
or data:approved:returnValues:contractAddress ilike '%0x0ADFb7975aa7c3aD90c57AEa8FDe5E31a721E9bb%'
or data:approved:returnValues:contractAddress ilike '%0x66423a1b45e14EaB8B132665FebC7Ec86BfcBF44%'
or data:approved:returnValues:contractAddress ilike '%axelar1aqcj54lzz0rk22gvqgcn8fr5tx4rzwdv5wv5j9dmnacgefvd7wzsy2j2mr%'
or data:approved:returnValues:contractAddress ilike '%0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8%'
or data:approved:returnValues:contractAddress ilike '%0xcbBA104B6CB4960a70E5dfc48E76C536A1f19609%'
or data:approved:returnValues:contractAddress ilike '%0xEac19c899098951fc6d0e6a7832b090474E2C292%')
and status = 'executed'
and simplified_status = 'received'
and (created_at::date >= '{start_date}' and created_at::date <= '{end_date}')
)

select "Platform",
count(distinct id) as "Transfer Count",
round(sum(amount)) as "Transfer Volume",
count(distinct user) as "Number of User",
round(count(distinct id)/count(distinct user)) as "Avg Transfer Count per User",
round(avg(amount),2) as "Avg Transfer Volume per Txn",
round((sum(amount)/count(distinct user)),2) as "Avg Transfer Volume per User"
from axelar_services
group by 1)

select "Platform", "Transfer Count", case
when "Transfer Volume" is null then 0 else "Transfer Volume" end as "Transfer Volume",
"Number of User", "Avg Transfer Count per User", case 
when "Avg Transfer Volume per Txn" is null then 0 else "Avg Transfer Volume per Txn" end as 
"Avg Transfer Volume per Txn", case 
when "Avg Transfer Volume per User" is null then 0 else "Avg Transfer Volume per User" end as 
"Avg Transfer Volume per User"
from overview 

"""

# --- Run Query (Row 1) ----------------------------------------------------------------------------------------------------------
df_overview = pd.read_sql(query_overview, conn)

# --- Row 1: Pie Charts for Platform Comparison ---------------------------------------------------------------------------
st.subheader("🔎Platforms Overview")
col1, col2, col3 = st.columns(3)

platform_colors = {
    "Squid": "#006ac9",
    "Interchain Token Service": "#00b3a0",
    "MintDAO Bridge": "#ffa7a7",
    "Prime Protocol": "#ff0000",
    "Nya Bridge": "#ff8000",
    "eesee.io": "#34f2a7",
    "The Junkyard": "#62cbff",
    "Rango Exchange": "#ffcf68"
}

# تابع تنظیمات مشترک
def style_pie_chart(fig, title):
    fig.update_traces(
        textinfo='percent+label',
        textposition='inside',
        insidetextorientation='radial',
        textfont_size=12
    )
    fig.update_layout(
        title=title,
        legend=dict(
            orientation="v",
            x=1,
            xanchor="left",
            y=0.5
        )
    )
    return fig

with col1:
    fig_pie1 = px.pie(
        df_overview,
        names="Platform",
        values="Transfer Count",
        color="Platform",
        color_discrete_map=platform_colors
    )
    fig_pie1 = style_pie_chart(fig_pie1, "Total Number of Transfers By Platform")
    st.plotly_chart(fig_pie1, use_container_width=True)

with col2:
    fig_pie2 = px.pie(
        df_overview,
        names="Platform",
        values="Transfer Volume",
        color="Platform",
        color_discrete_map=platform_colors
    )
    fig_pie2 = style_pie_chart(fig_pie2, "Total Volume of Transfers By Platform (USD)")
    st.plotly_chart(fig_pie2, use_container_width=True)

with col3:
    fig_pie3 = px.pie(
        df_overview,
        names="Platform",
        values="Number of User",
        color="Platform",
        color_discrete_map=platform_colors
    )
    fig_pie3 = style_pie_chart(fig_pie3, "Total Number of Users By Platform")
    st.plotly_chart(fig_pie3, use_container_width=True)


# --- Dynamic SQL based on filters (Row2,3,4) -------------------------------------------------------------------------------------
query = f"""
with axelar_services as (
select created_at, data:send:amount * data:link:price as amount, recipient_address as user, 
id, 'Token Transfers' as service, case 
when sender_address ilike '%0xce16F69375520ab01377ce7B88f5BA8C48F8D666%' then 'Squid'
when sender_address ilike '%0xdf4fFDa22270c12d0b5b3788F1669D709476111E%' then 'Squid'
when sender_address ilike '%0xB5FB4BE02232B1bBA4dC8f81dc24C26980dE9e3C%' then 'Interchain Token Service'
when sender_address ilike '%0xD0FFD6fE14b2037897Ad8cD072F6d6DE30CF8e56%' then 'MintDAO Bridge'
when sender_address ilike '%0xbe54BaFC56B468d4D20D609F0Cf17fFc56b99913%' then 'Prime Protocol'
when sender_address ilike '%0x0ADFb7975aa7c3aD90c57AEa8FDe5E31a721E9bb%' then 'Rango Exchange'
when sender_address ilike '%0x66423a1b45e14EaB8B132665FebC7Ec86BfcBF44%' then 'The Junkyard'
when sender_address ilike '%axelar1aqcj54lzz0rk22gvqgcn8fr5tx4rzwdv5wv5j9dmnacgefvd7wzsy2j2mr%' then 'Interchain Token Service'
when sender_address ilike '%0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8%' then 'Squid'
when sender_address ilike '%0xcbBA104B6CB4960a70E5dfc48E76C536A1f19609%' then 'Nya Bridge'
when sender_address ilike '%0xEac19c899098951fc6d0e6a7832b090474E2C292%' then 'eesee.io'
end as "Platform"
from axelar.axelscan.fact_transfers
where (sender_address ilike '%0xce16F69375520ab01377ce7B88f5BA8C48F8D666%'
or sender_address ilike '%0xdf4fFDa22270c12d0b5b3788F1669D709476111E%'
or sender_address ilike '%0xB5FB4BE02232B1bBA4dC8f81dc24C26980dE9e3C%'
or sender_address ilike '%0xD0FFD6fE14b2037897Ad8cD072F6d6DE30CF8e56%'
or sender_address ilike '%0xbe54BaFC56B468d4D20D609F0Cf17fFc56b99913%'
or sender_address ilike '%0x0ADFb7975aa7c3aD90c57AEa8FDe5E31a721E9bb%'
or sender_address ilike '%0x66423a1b45e14EaB8B132665FebC7Ec86BfcBF44%'
or sender_address ilike '%axelar1aqcj54lzz0rk22gvqgcn8fr5tx4rzwdv5wv5j9dmnacgefvd7wzsy2j2mr%'
or sender_address ilike '%0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8%'
or sender_address ilike '%0xcbBA104B6CB4960a70E5dfc48E76C536A1f19609%'
or sender_address ilike '%0xEac19c899098951fc6d0e6a7832b090474E2C292%')
and status='executed'
and simplified_status='received'
and (created_at::date >= '{start_date}' and created_at::date <= '{end_date}')

union all

select created_at, data:value as amount, 
to_varchar(data:call:transaction:from) as user,
to_varchar(id) as id, 'GMP' as service, case 
when data:approved:returnValues:contractAddress ilike '%0xce16F69375520ab01377ce7B88f5BA8C48F8D666%' then 'Squid'
when data:approved:returnValues:contractAddress ilike '%0xdf4fFDa22270c12d0b5b3788F1669D709476111E%' then 'Squid'
when data:approved:returnValues:contractAddress ilike '%0xB5FB4BE02232B1bBA4dC8f81dc24C26980dE9e3C%' then 'Interchain Token Service'
when data:approved:returnValues:contractAddress ilike '%0xD0FFD6fE14b2037897Ad8cD072F6d6DE30CF8e56%' then 'MintDAO Bridge'
when data:approved:returnValues:contractAddress ilike '%0xbe54BaFC56B468d4D20D609F0Cf17fFc56b99913%' then 'Prime Protocol'
when data:approved:returnValues:contractAddress ilike '%0x0ADFb7975aa7c3aD90c57AEa8FDe5E31a721E9bb%' then 'Rango Exchange'
when data:approved:returnValues:contractAddress ilike '%0x66423a1b45e14EaB8B132665FebC7Ec86BfcBF44%' then 'The Junkyard'
when data:approved:returnValues:contractAddress ilike '%axelar1aqcj54lzz0rk22gvqgcn8fr5tx4rzwdv5wv5j9dmnacgefvd7wzsy2j2mr%' then 'Interchain Token Service'
when data:approved:returnValues:contractAddress ilike '%0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8%' then 'Squid'
when data:approved:returnValues:contractAddress ilike '%0xcbBA104B6CB4960a70E5dfc48E76C536A1f19609%' then 'Nya Bridge'
when data:approved:returnValues:contractAddress ilike '%0xEac19c899098951fc6d0e6a7832b090474E2C292%' then 'eesee.io'
end as "Platform"
from axelar.axelscan.fact_gmp
where (data:approved:returnValues:contractAddress ilike '%0xce16F69375520ab01377ce7B88f5BA8C48F8D666%'
or data:approved:returnValues:contractAddress ilike '%0xdf4fFDa22270c12d0b5b3788F1669D709476111E%'
or data:approved:returnValues:contractAddress ilike '%0xB5FB4BE02232B1bBA4dC8f81dc24C26980dE9e3C%'
or data:approved:returnValues:contractAddress ilike '%0xD0FFD6fE14b2037897Ad8cD072F6d6DE30CF8e56%'
or data:approved:returnValues:contractAddress ilike '%0xbe54BaFC56B468d4D20D609F0Cf17fFc56b99913%'
or data:approved:returnValues:contractAddress ilike '%0x0ADFb7975aa7c3aD90c57AEa8FDe5E31a721E9bb%'
or data:approved:returnValues:contractAddress ilike '%0x66423a1b45e14EaB8B132665FebC7Ec86BfcBF44%'
or data:approved:returnValues:contractAddress ilike '%axelar1aqcj54lzz0rk22gvqgcn8fr5tx4rzwdv5wv5j9dmnacgefvd7wzsy2j2mr%'
or data:approved:returnValues:contractAddress ilike '%0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8%'
or data:approved:returnValues:contractAddress ilike '%0xcbBA104B6CB4960a70E5dfc48E76C536A1f19609%'
or data:approved:returnValues:contractAddress ilike '%0xEac19c899098951fc6d0e6a7832b090474E2C292%')
and status = 'executed'
and simplified_status = 'received'
and (created_at::date >= '{start_date}' and created_at::date <= '{end_date}')
)

select date_trunc('{timeframe}', created_at) as "Date", "Platform",
       count(distinct id) as "Transfer Count",
       sum(amount) as "Transfer Volume",
       count(distinct user) as "Number of User",
       round(count(distinct id)/count(distinct user)) as "Avg Transfer Count per User",
       round(avg(amount),2) as "Avg Transfer Volume per Txn",
       round((sum(amount)/count(distinct user)),2) as "Avg Transfer Volume per User"
from axelar_services
group by 1, 2
order by 1
"""

# --- Run Query(Row2,3,4) --------------------------------------------------------------------------------------------------------
df = pd.read_sql(query, conn)

# --- Row 2: Stacked Bar Charts ---------------------------------------------------------------------------------------
st.subheader("📊Transfers By Platform Over Time")

col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(df, x="Date", y="Transfer Volume", color="Platform", title="Volume of Transfers By Platform Over Time ($USD)",
                  labels={"Volume": "$USD"}, barmode="stack")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.bar(df, x="Date", y="Transfer Count", color="Platform", title="Number of Transfers By Platform Over Time",
                  labels={"Count": "Txns count"}, barmode="stack")
    st.plotly_chart(fig2, use_container_width=True)

# --- Row 3: Line Chart & Scatter Chart --------------------------------------------------------------------------------

col3, col4 = st.columns(2)

with col3:
    fig3 = px.line(df, x="Date", y="Number of User", color="Platform", title="Number of Users By Platform Over Time",
                  labels={"Number of User": "Address count"})
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    fig4 = px.scatter(df, x="Date", y="Avg Transfer Count per User", color="Platform",
                      title="Avg Transfers Count per User Over Time",
                      labels={"Avg Transfer Count per User": "Txns count"})
    st.plotly_chart(fig4, use_container_width=True)

# --- Row 4: Area Charts -----------------------------------------------------------------------------------------------

col5, col6 = st.columns(2)

with col5:
    fig5 = px.area(
        df,
        x="Date",
        y="Avg Transfer Volume per User",
        color="Platform",
        title="Avg Transfers Volume per User Over Time",
        labels={"Avg Transfer Volume per User": "USD"}
    )
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    fig6 = px.area(
        df,
        x="Date",
        y="Avg Transfer Volume per Txn",
        color="Platform",
        title="Avg Transfers Volume per Transaction Over Time",
        labels={"Avg Transfer Volume per Txn": "USD"}
    )
    st.plotly_chart(fig6, use_container_width=True)
