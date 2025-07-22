import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import plotly.graph_objs as go

st.set_page_config(layout="wide")
st.title("📈 Bitcoin Technical Analysis Dashboard")

# -- Fetch OHLCV data
@st.cache_data(ttl=300)
def get_data():
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=200)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

df = get_data()

# -- Add indicators
df['EMA20'] = ta.ema(df['close'], length=20)
df['EMA50'] = ta.ema(df['close'], length=50)
df['RSI'] = ta.rsi(df['close'])
macd = ta.macd(df['close'])
df = pd.concat([df, macd], axis=1)

# -- Signal logic
def generate_signal(row):
    if row['RSI'] < 30 and row['MACD_12_26_9'] > row['MACDs_12_26_9']:
        return 'BUY'
    elif row['RSI'] > 70 and row['MACD_12_26_9'] < row['MACDs_12_26_9']:
        return 'SELL'
    else:
        return ''

df['signal'] = df.apply(generate_signal, axis=1)

# -- Candlestick + Indicators Plot
fig = go.Figure()

fig.add_trace(go.Candlestick(x=df['timestamp'],
                             open=df['open'], high=df['high'],
                             low=df['low'], close=df['close'],
                             name='Candles'))

fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA20'], line=dict(color='blue'), name='EMA20'))
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA50'], line=dict(color='orange'), name='EMA50'))

# -- Signal markers
signal_df = df[df['signal'] != '']
fig.add_trace(go.Scatter(
    x=signal_df['timestamp'],
    y=signal_df['close'],
    mode='markers+text',
    marker=dict(size=10, color=signal_df['signal'].map({'BUY': 'green', 'SELL': 'red'})),
    text=signal_df['signal'],
    textposition='top center',
    name='Signals'
))

fig.update_layout(xaxis_rangeslider_visible=False, height=600)

# -- Show chart
st.plotly_chart(fig, use_container_width=True)

# -- RSI plot
st.subheader("RSI Indicator")
st.line_chart(df.set_index('timestamp')['RSI'])

# -- Data preview
if st.checkbox("Show raw data"):
    st.write(df.tail(20))

