# intraday_signals_dashboard.py

import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import time
from datetime import datetime
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import warnings

# Suppress warnings for cleaner dashboard
warnings.simplefilter(action='ignore', category=FutureWarning)

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="📊 Intraday Stock Signals", layout="wide")

st.title("📈 Intraday Stock Signals Dashboard")

# ----------------------------
# AUTO REFRESH (every 5 min)
# ----------------------------
st_autorefresh(interval=5 * 60 * 1000, key="data_refresh")  # interval in ms

# ----------------------------
# USER INPUTS
# ----------------------------
symbols_input = st.text_input(
    "Enter stock symbols (comma separated, e.g., TCS.NS,INFY.NS):",
    "TCS.NS,INFY.NS,RELIANCE.NS,HDFCBANK.NS"
)
interval = st.selectbox("Select interval", ["1m", "5m", "15m", "30m", "60m"], index=1)

symbols = [sym.strip() for sym in symbols_input.split(",")]

# ----------------------------
# FUNCTIONS
# ----------------------------
def get_data(symbol, interval="5m"):
    df = yf.download(symbol, period="5d", interval=interval, auto_adjust=True)
    df = df.reset_index()
    df.columns = [col.replace(" ", "_") for col in df.columns]
    return df

def compute_indicators(df):
    df["SMA_20"] = ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator()
    df["SMA_50"] = ta.trend.SMAIndicator(df["Close"], window=50).sma_indicator()
    df["RSI_14"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    return df

def get_signal(row):
    """Simple rule-based signal"""
    if row["SMA_20"] > row["SMA_50"] and row["RSI_14"] < 70:
        return "BUY"
    elif row["SMA_20"] < row["SMA_50"] and row["RSI_14"] > 30:
        return "SELL"
    else:
        return "HOLD"

def plot_stock(df, symbol):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["Datetime"],
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name=symbol
    ))
    fig.add_trace(go.Scatter(
        x=df["Datetime"], y=df["SMA_20"], mode="lines", name="SMA 20"
    ))
    fig.add_trace(go.Scatter(
        x=df["Datetime"], y=df["SMA_50"], mode="lines", name="SMA 50"
    ))
    fig.update_layout(
        title=f"{symbol} Candlestick Chart with SMA",
        xaxis_title="Datetime",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# MAIN DASHBOARD
# ----------------------------
for symbol in symbols:
    st.subheader(f"🔹 {symbol}")
    try:
        df = get_data(symbol, interval)
        df = compute_indicators(df)
        last_row = df.iloc[-1]
        signal = get_signal(last_row)

        st.metric(label="Current Signal", value=signal)
        st.write(df.tail(5))  # show last 5 rows
        plot_stock(df, symbol)
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")

st.markdown("---")
st.caption(f"Dashboard last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
