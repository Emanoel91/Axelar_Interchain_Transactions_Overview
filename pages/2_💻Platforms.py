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
st.title("🚀Platforms Powered By Axelar")

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

# ------------------------------------------------------------------------------------------------------------------------
# --- Dynamic SQL based on filters -------------------------------------------------------------------------------------
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

# --- Run Query --------------------------------------------------------------------------------------------------------
df = pd.read_sql(query, conn)

# --- Row 1: Stacked Bar Charts ---------------------------------------------------------------------------------------
st.subheader("📦 Transfer Volume & Count by Platform")

col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(df, x="Date", y="Transfer Volume", color="Platform", title="Transfer Volume by Platform",
                  labels={"Transfer Volume": "Volume"}, barmode="stack")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.bar(df, x="Date", y="Transfer Count", color="Platform", title="Transfer Count by Platform",
                  labels={"Transfer Count": "Count"}, barmode="stack")
    st.plotly_chart(fig2, use_container_width=True)

# --- Row 2: Line Chart & Scatter Chart --------------------------------------------------------------------------------
st.subheader("👥 User Count & Transfer Behavior by Platform")

col3, col4 = st.columns(2)

with col3:
    fig3 = px.line(df, x="Date", y="Number of User", color="Platform", title="Number of Users Over Time")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    fig4 = px.scatter(df, x="Date", y="Avg Transfer Count per User", color="Platform",
                      title="Avg Transfers per User Over Time")
    st.plotly_chart(fig4, use_container_width=True)

# --- Row 3: Area Charts -----------------------------------------------------------------------------------------------
st.subheader("📈 Transfer Volume Trends by Platform")

col5, col6 = st.columns(2)

with col5:
    fig5 = px.area(df, x="Date", y="Avg Transfer Volume per User", color="Platform",
                   title="Avg Transfer Volume per User")
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    fig6 = px.area(df, x="Date", y="Avg Transfer Volume per Txn", color="Platform",
                   title="Avg Transfer Volume per Transaction")
    st.plotly_chart(fig6, use_container_width=True)


