import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import time

# --------------------------------------------
# PAGE SETUP
# --------------------------------------------
st.set_page_config(page_title="📊 Intraday Signal Dashboard", layout="wide")
st.title("📊 Intraday Technical Signal Dashboard (Live Refresh)")
st.caption("Auto-refreshes every few minutes using free Yahoo Finance data")

# --------------------------------------------
# USER INPUTS
# --------------------------------------------
default_symbols = ["RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "TCS.NS", "ICICIBANK.NS"]
symbols = st.multiselect("Select stocks:", default_symbols, default=default_symbols)
interval = st.selectbox("Interval", ["1m", "5m", "15m", "30m", "1h", "1d"], index=2)
refresh_rate = st.slider("Refresh (seconds)", 30, 300, 120)

# --------------------------------------------
# FETCH DATA
# --------------------------------------------
def get_data(symbol):
    df = yf.download(symbol, period="5d", interval=interval)
    df = df.reset_index()
    df.columns = [col.replace(" ", "_") for col in df.columns]
    df["Close"] = df["Close"].astype(float).squeeze()  # ensure 1D
    return df

# --------------------------------------------
# INDICATOR CALCULATION
# --------------------------------------------
def compute_indicators(df):
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
    stoch = ta.momentum.StochasticOscillator(df["High"], df["Low"], df["Close"])
    df["Stochastic"] = stoch.stoch()
    df["MACD"] = ta.trend.MACD(df["Close"]).macd()
    df["EMA_20"] = ta.trend.EMAIndicator(df["Close"], window=20).ema_indicator()
    df["EMA_50"] = ta.trend.EMAIndicator(df["Close"], window=50).ema_indicator()
    df["BB_High"] = ta.volatility.BollingerBands(df["Close"]).bollinger_hband()
    df["BB_Low"] = ta.volatility.BollingerBands(df["Close"]).bollinger_lband()
    return df

# --------------------------------------------
# SIGNAL LOGIC
# --------------------------------------------
def get_signal(row):
    signals = []
    if row["RSI"] < 30:
        signals.append("RSI Oversold")
    elif row["RSI"] > 70:
        signals.append("RSI Overbought")
    if row["Close"] > row["EMA_20"] and row["EMA_20"] > row["EMA_50"]:
        signals.append("Bullish EMA Cross")
    elif row["Close"] < row["EMA_20"] and row["EMA_20"] < row["EMA_50"]:
        signals.append("Bearish EMA Cross")
    if row["Close"] < row["BB_Low"]:
        signals.append("Bollinger Buy")
    elif row["Close"] > row["BB_High"]:
        signals.append("Bollinger Sell")

    if len(signals) == 0:
        return "Neutral"
    elif "Buy" in " ".join(signals) or "Oversold" in " ".join(signals) or "Bullish" in " ".join(signals):
        return "BUY"
    elif "Sell" in " ".join(signals) or "Overbought" in " ".join(signals) or "Bearish" in " ".join(signals):
        return "SELL"
    else:
        return "Neutral"

# --------------------------------------------
# MAIN LOGIC
# --------------------------------------------
placeholder = st.empty()

while True:
    all_data = []
    for symbol in symbols:
        df = get_data(symbol)
        df = compute_indicators(df)
        last = df.iloc[-1]
        signal = get_signal(last)
        all_data.append({
            "Symbol": symbol,
            "Last Price": round(last["Close"], 2),
            "RSI": round(last["RSI"], 2),
            "MACD": round(last["MACD"], 2),
            "Signal": signal
        })

    result = pd.DataFrame(all_data)
    with placeholder.container():
        st.dataframe(result, use_container_width=True)
        st.info(f"Last updated at {time.strftime('%H:%M:%S')}. Auto-refreshing every {refresh_rate}s.")
    time.sleep(refresh_rate)
