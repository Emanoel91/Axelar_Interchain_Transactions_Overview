import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# --- Page Config ---
st.set_page_config(
    page_title="Axelar : Interchain Transactions Overview",
    page_icon="https://img.cryptorank.io/coins/axelar1663924228506.png",
    layout="wide"
)

st.title("💻 Platforms Powered By Axelar")
st.info("📊 Charts initially display data for a default time range. Select a custom range to view results for your desired period.")
st.info("⏳ On-chain data retrieval may take a few moments. Please wait while the results load.")

timeframe = st.selectbox("Select Time Frame", ["month", "week", "day"])
start_date = st.date_input("Start Date", value=pd.to_datetime("2023-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("2025-07-31"))

@st.cache_data(ttl=600)
def load_data():
    url = "https://api.dune.com/api/v1/query/5575605/results?api_key=kmCBMTxWKBxn6CVgCXhwDvcFL1fBp6rO"
    response = requests.get(url)
    data = response.json()
    rows = data.get('result', {}).get('rows', [])
    if not rows:
        st.error("API response does not contain data rows!")
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if 'date' not in df.columns:
        st.error("Column 'date' not found in data!")
        return pd.DataFrame()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df

df = load_data()

# تبدیل start_date و end_date به pd.Timestamp
start_date = pd.Timestamp(start_date)
end_date = pd.Timestamp(end_date)

# فیلتر کردن دیتا بر اساس تاریخ
df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

def resample_df(df, timeframe):
    if timeframe == "day":
        df_resampled = df.copy()
    else:
        freq_map = {"week": "W", "month": "M"}
        freq = freq_map.get(timeframe, "D")  # Default day if not found
        df['period'] = df['date'].dt.to_period(freq).dt.start_time
        df_resampled = df.groupby(['period', 'platform']).agg({
            'num_txs': 'sum',
            'volume': 'sum'
        }).reset_index()
        df_resampled.rename(columns={'period': 'date'}, inplace=True)
    return df_resampled

df_resampled = resample_df(df, timeframe)

# ردیف اول: دو stacked bar chart
col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(
        df_resampled,
        x='date',
        y='num_txs',
        color='platform',
        title="Number of Transactions by Platform Over Time",
        labels={'date': 'Date', 'num_txs': 'Number of Transactions'},
        barmode='stack'
    )
    fig1.update_layout(xaxis_title='Date', yaxis_title='Number of Transactions')
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.bar(
        df_resampled,
        x='date',
        y='volume',
        color='platform',
        title="Volume of Transactions by Platform Over Time",
        labels={'date': 'Date', 'volume': 'Transaction Volume'},
        barmode='stack'
    )
    fig2.update_layout(xaxis_title='Date', yaxis_title='Transaction Volume')
    st.plotly_chart(fig2, use_container_width=True)

# ردیف دوم: دو نمودار خطی تجمعی
df_resampled = df_resampled.sort_values('date')
df_resampled['cumulative_num_txs'] = df_resampled.groupby('platform')['num_txs'].cumsum()
df_resampled['cumulative_volume'] = df_resampled.groupby('platform')['volume'].cumsum()

col3, col4 = st.columns(2)

with col3:
    fig3 = px.line(
        df_resampled,
        x='date',
        y='cumulative_volume',
        color='platform',
        title="Cumulative Transaction Volume by Platform Over Time",
        labels={'date': 'Date', 'cumulative_volume': 'Cumulative Volume'}
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    fig4 = px.line(
        df_resampled,
        x='date',
        y='cumulative_num_txs',
        color='platform',
        title="Cumulative Number of Transactions by Platform Over Time",
        labels={'date': 'Date', 'cumulative_num_txs': 'Cumulative Number of Transactions'}
    )
    st.plotly_chart(fig4, use_container_width=True)

# ردیف سوم: دو bar chart مجموع کل برای هر پلتفرم با مقدار روی ستون‌ها
df_total = df.groupby('platform').agg({
    'num_txs': 'sum',
    'volume': 'sum'
}).reset_index()

col5, col6 = st.columns(2)

with col5:
    fig5 = px.bar(
        df_total,
        x='platform',
        y='num_txs',
        text='num_txs',
        title="Total Number of Transactions per Platform",
        labels={'num_txs': 'Number of Transactions', 'platform': 'Platform'},
        color='platform'
    )
    fig5.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    fig5.update_layout(yaxis_range=[0, df_total['num_txs'].max()*1.1])
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    fig6 = px.bar(
        df_total,
        x='platform',
        y='volume',
        text='volume',
        title="Total Volume of Transactions per Platform",
        labels={'volume': 'Volume', 'platform': 'Platform'},
        color='platform'
    )
    fig6.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig6.update_layout(yaxis_range=[0, df_total['volume'].max()*1.1])
    st.plotly_chart(fig6, use_container_width=True)
