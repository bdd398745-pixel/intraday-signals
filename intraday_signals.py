import streamlit as st
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator, StochasticOscillator, StochRSIIndicator, ROCIndicator
from ta.trend import MACD, CCIIndicator, ADXIndicator
from ta.volume import VolumeWeightedAveragePrice
import time

# --------------------------------------------
# STREAMLIT PAGE SETUP
# --------------------------------------------
st.set_page_config(page_title="Intraday Indicator Signals", layout="wide")
st.title("📊 Intraday Technical Signal Dashboard (Free Live Refresh)")
st.caption("Data updates every few minutes from Yahoo Finance (5–10 min delay).")

# --------------------------------------------
# SELECT STOCK
# --------------------------------------------
ticker = st.text_input("Enter NSE Stock Symbol", "RELIANCE.NS")
refresh_rate = st.slider("Auto-refresh (minutes)", 1, 10, 3)

# --------------------------------------------
# AUTO REFRESH
# --------------------------------------------
st_autorefresh = st.experimental_rerun
st_autorefresh_counter = st.experimental_memo.clear
placeholder = st.empty()

# --------------------------------------------
# DATA FETCHING FUNCTION
# --------------------------------------------
@st.cache_data(ttl=60 * refresh_rate)
def load_data(ticker):
    df = yf.download(ticker, period="1d", interval="5m")
    return df.dropna()

# --------------------------------------------
# LOOP (simulate live feed)
# --------------------------------------------
df = load_data(ticker)
if df.empty:
    st.warning("No data fetched. Try another symbol like TCS.NS or INFY.NS.")
else:
    # --- Indicators ---
    df["RSI"] = RSIIndicator(df["Close"], window=14).rsi()
    df["%K"] = StochasticOscillator(df["High"], df["Low"], df["Close"], window=9, smooth_window=6).stoch()
    df["StochRSI"] = StochRSIIndicator(df["Close"], window=14).stochrsi()
    macd = MACD(df["Close"], window_slow=26, window_fast=12, window_sign=9)
    df["MACD"], df["Signal"] = macd.macd(), macd.macd_signal()
    adx = ADXIndicator(df["High"], df["Low"], df["Close"], window=14)
    df["ADX"], df["DI+"] , df["DI-"] = adx.adx(), adx.adx_pos(), adx.adx_neg()
    df["WilliamsR"] = (df["High"].rolling(14).max() - df["Close"]) / (df["High"].rolling(14).max() - df["Low"].rolling(14).min()) * -100
    df["CCI"] = CCIIndicator(df["High"], df["Low"], df["Close"], window=14).cci()
    df["ROC"] = ROCIndicator(df["Close"], window=12).roc()
    df["EMA13"] = df["Close"].ewm(span=13, adjust=False).mean()
    df["BullBear"] = df["High"] - df["EMA13"]

    last = df.iloc[-1]

    # --- SIGNAL CONDITIONS ---
    def sig(val, low, high, buy_below=True):
        if buy_below and val < low: return "BUY"
        if not buy_below and val > high: return "BUY"
        if val > high: return "SELL"
        if val < low: return "BUY"
        return "NEUTRAL"

    signals = {
        "RSI (14)": "BUY" if last.RSI < 30 else "SELL" if last.RSI > 70 else "NEUTRAL",
        "Stochastic (9,6)": "BUY" if last["%K"] < 20 else "SELL" if last["%K"] > 80 else "NEUTRAL",
        "Stoch RSI (14)": "BUY" if last.StochRSI < 0.2 else "SELL" if last.StochRSI > 0.8 else "NEUTRAL",
        "MACD (12,26)": "BUY" if last.MACD > last.Signal else "SELL" if last.MACD < last.Signal else "NEUTRAL",
        "ADX (14)": "BUY" if last.ADX > 25 and last["DI+"] > last["DI-"] else "SELL" if last.ADX > 25 else "NEUTRAL",
        "Williams %R": "BUY" if last.WilliamsR < -80 else "SELL" if last.WilliamsR > -20 else "NEUTRAL",
        "CCI (14)": "BUY" if last.CCI < -100 else "SELL" if last.CCI > 100 else "NEUTRAL",
        "ROC (12)": "BUY" if last.ROC > 0 else "SELL" if last.ROC < 0 else "NEUTRAL",
        "Bull/Bear Power (13)": "BUY" if last.BullBear > 0 else "SELL" if last.BullBear < 0 else "NEUTRAL",
    }

    # --- DISPLAY ---
    st.subheader(f"📈 {ticker} — Latest Intraday Signals")
    signal_df = pd.DataFrame(list(signals.items()), columns=["Indicator", "Signal"])
    st.dataframe(signal_df, hide_index=True, use_container_width=True)

    # --- PLOT ---
    st.line_chart(df["Close"], height=250)

    st.success(f"✅ Last updated: {df.index[-1].strftime('%H:%M:%S')} — auto-refresh every {refresh_rate} min")

