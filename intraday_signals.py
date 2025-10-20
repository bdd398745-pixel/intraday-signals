import streamlit as st
import yfinance as yf
import ta
from datetime import datetime
import time
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import warnings

warnings.filterwarnings("ignore")

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="Intraday Stock Signals", layout="wide")

# Auto-refresh every 5 minutes
st_autorefresh(interval=5 * 60 * 1000, key="data_refresh")

st.title("📊 Intraday Stock Signal Dashboard")

# ----------------------------
# USER INPUTS
# ----------------------------
symbol = st.text_input("Enter Stock Symbol (e.g., TCS.NS, INFY.NS)", value="TCS.NS")
interval = st.selectbox("Select Interval", ["1m", "5m", "15m", "30m", "60m"], index=1)
period = "5d"

# ----------------------------
# FETCH DATA
# ----------------------------
df = yf.download(symbol, period=period, interval=interval)
if df.empty:
    st.warning("No data found for the symbol!")
    st.stop()

# ----------------------------
# INDICATORS
# ----------------------------
df["SMA_20"] = ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator()
df["EMA_20"] = ta.trend.EMAIndicator(df["Close"], window=20).ema_indicator()

# ----------------------------
# PLOT CANDLESTICK WITH INDICATORS
# ----------------------------
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name='Candlestick'
))

fig.add_trace(go.Scatter(
    x=df.index,
    y=df["SMA_20"],
    line=dict(color='blue', width=1),
    name='SMA 20'
))

fig.add_trace(go.Scatter(
    x=df.index,
    y=df["EMA_20"],
    line=dict(color='orange', width=1),
    name='EMA 20'
))

fig.update_layout(
    title=f"{symbol} Intraday Chart",
    xaxis_title="Time",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False,
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# SIMPLE SIGNALS
# ----------------------------
latest_close = df["Close"].iloc[-1]
latest_sma = df["SMA_20"].iloc[-1]
latest_ema = df["EMA_20"].iloc[-1]

signal = "HOLD"
if latest_close > latest_sma and latest_close > latest_ema:
    signal = "BUY"
elif latest_close < latest_sma and latest_close < latest_ema:
    signal = "SELL"

st.metric(label="Latest Price", value=round(latest_close, 2))
st.metric(label="Signal", value=signal)
