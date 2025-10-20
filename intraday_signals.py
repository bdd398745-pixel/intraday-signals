# intraday_signals_app.py

import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime
import time

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="📊 Intraday Signal Dashboard", layout="wide")
st.title("📊 Intraday Signal Dashboard")

# ----------------------------
# AUTO REFRESH SETUP
# ----------------------------
refresh_time = st.sidebar.number_input("Refresh every (seconds)", min_value=10, value=60)

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > refresh_time:
    st.session_state.last_refresh = time.time()
    st.experimental_rerun()

# ----------------------------
# USER INPUTS
# ----------------------------
symbols_input = st.sidebar.text_area(
    "Enter stock symbols separated by comma (e.g., TCS.NS, INFY.NS, RELIANCE.NS)",
    value="TCS.NS, INFY.NS, RELIANCE.NS"
)
symbols = [s.strip() for s in symbols_input.split(",")]

interval = st.sidebar.selectbox(
    "Select interval", ["1m", "5m", "15m", "30m", "60m", "1d"], index=1
)

# ----------------------------
# DATA FUNCTIONS
# ----------------------------
def get_data(symbol):
    try:
        df = yf.download(symbol, period="5d", interval=interval)
        if df.empty:
            return None
        df = df.reset_index()
        df.columns = [col.replace(" ", "_") for col in df.columns]  # clean column names
        df["Close"] = df["Close"].astype(float)
        return df
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")
        return None

def compute_indicators(df):
    # Bollinger Bands
    bb_indicator = ta.volatility.BollingerBands(close=df["Close"], window=20, window_dev=2)
    df["bb_high"] = bb_indicator.bollinger_hband()
    df["bb_low"] = bb_indicator.bollinger_lband()

    # RSI
    df["rsi"] = ta.momentum.RSIIndicator(close=df["Close"], window=14).rsi()

    # Moving averages
    df["ma20"] = df["Close"].rolling(window=20).mean()
    df["ma50"] = df["Close"].rolling(window=50).mean()

    return df

def get_signal(last_row):
    signals = []
    # Simple strategy
    if last_row["Close"] > last_row["bb_high"]:
        signals.append("Sell (Price above BB high)")
    elif last_row["Close"] < last_row["bb_low"]:
        signals.append("Buy (Price below BB low)")
    
    if last_row["rsi"] > 70:
        signals.append("Sell (RSI > 70)")
    elif last_row["rsi"] < 30:
        signals.append("Buy (RSI < 30)")

    if last_row["ma20"] > last_row["ma50"]:
        signals.append("Trend Up")
    else:
        signals.append("Trend Down")

    return ", ".join(signals) if signals else "Hold"

# ----------------------------
# MAIN DASHBOARD
# ----------------------------
all_data = []

for symbol in symbols:
    df = get_data(symbol)
    if df is not None:
        df = compute_indicators(df)
        last = df.iloc[-1]
        signal = get_signal(last)
        all_data.append({
            "Symbol": symbol,
            "Last Close": last["Close"],
            "RSI": round(last["rsi"], 2),
            "BB High": round(last["bb_high"], 2),
            "BB Low": round(last["bb_low"], 2),
            "MA20": round(last["ma20"], 2),
            "MA50": round(last["ma50"], 2),
            "Signal": signal,
            "Time": last["Datetime"]
        })

if all_data:
    result_df = pd.DataFrame(all_data)
    st.dataframe(result_df)
else:
    st.warning("No data available. Check your symbols or interval.")
