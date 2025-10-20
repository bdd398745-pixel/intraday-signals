# intraday_signals_app.py
import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="Intraday Stock Signals", layout="wide")
st.title("Intraday Stock Buy/Sell Signals")

# ----------------------------
# USER INPUTS
# ----------------------------
symbols_input = st.text_area(
    "Enter stock symbols (comma separated)", 
    value="RELIANCE.NS, TCS.NS, INFY.NS"
)
symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

interval = st.selectbox("Select interval", ["1m", "5m", "15m", "30m", "1h", "1d"], index=1)
refresh_time = st.number_input("Refresh every (seconds)", min_value=10, value=60)

# ----------------------------
# AUTO REFRESH
# ----------------------------
st_autorefresh(interval=refresh_time*1000, limit=None, key="refresh")

# ----------------------------
# FUNCTIONS
# ----------------------------
def get_data(symbol):
    """Fetch historical intraday data safely"""
    try:
        df = yf.download(symbol, period="5d", interval=interval, progress=False)
        if isinstance(df, tuple):  # some versions return (data, metadata)
            df = df[0]
        df = df.reset_index()
        df.columns = [str(col).replace(" ", "_") for col in df.columns]
        df["Close"] = df["Close"].astype(float).squeeze()
        return df
    except Exception as e:
        st.warning(f"Could not fetch {symbol}: {e}")
        return pd.DataFrame()

def compute_indicators(df):
    """Add RSI, MACD, and Stochastic RSI indicators"""
    if df.empty or len(df) < 14:
        return df
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi().fillna(0)
    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd().fillna(0)
    df["MACD_Signal"] = macd.macd_signal().fillna(0)
    df["StochRSI"] = ta.momentum.StochRSIIndicator(df["Close"]).stochrsi().fillna(0)
    return df

def get_signal(last_row):
    """Generate a simple Buy/Sell signal based on indicators"""
    if last_row.empty:
        return "No Data"
    rsi = last_row["RSI"]
    macd = last_row["MACD"]
    macd_signal = last_row["MACD_Signal"]
    stochrsi = last_row["StochRSI"]

    if rsi < 30 and macd > macd_signal and stochrsi < 0.2:
        return "BUY"
    elif rsi > 70 and macd < macd_signal and stochrsi > 0.8:
        return "SELL"
    else:
        return "HOLD"

# ----------------------------
# PROCESS & DISPLAY SIGNALS
# ----------------------------
all_signals = []

for symbol in symbols:
    df = get_data(symbol)
    if df.empty:
        continue
    df = compute_indicators(df)
    last = df.iloc[-1]
    signal = get_signal(last)
    all_signals.append({
        "Symbol": symbol,
        "Datetime": last["Datetime"] if "Datetime" in last else last.name,
        "Close": last["Close"],
        "Signal": signal
    })

if all_signals:
    signals_df = pd.DataFrame(all_signals)
    st.dataframe(signals_df)
else:
    st.info("No data to display. Check symbols or try again later.")
