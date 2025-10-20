import streamlit as st
import pandas as pd
import yfinance as yf
from ta.momentum import (
    RSIIndicator,
    StochasticOscillator,
    StochRSIIndicator,
    ROCIndicator,
    WilliamsRIndicator,
)
from ta.trend import MACD, CCIIndicator, ADXIndicator
from ta.volume import VolumeWeightedAveragePrice
from ta.others import UltimateOscillator
from streamlit_autorefresh import st_autorefresh

# --------------------------------------------
# PAGE CONFIG
# --------------------------------------------
st.set_page_config(page_title="Intraday Indicator Signals", layout="wide")
st.title("📊 Intraday Technical Signal Dashboard (Free Live Refresh)")
st.caption("⏱ Live data (delayed 5–10 mins) from Yahoo Finance • Auto-refresh enabled")

# --------------------------------------------
# USER INPUTS
# --------------------------------------------
col1, col2 = st.columns(2)
ticker = col1.text_input("Enter NSE Stock Symbol", "RELIANCE.NS")
refresh_rate = col2.slider("Auto-refresh interval (minutes)", 1, 10, 3)

# Auto refresh setup
st_autorefresh(interval=refresh_rate * 60 * 1000, limit=None, key="data_refresh")

# --------------------------------------------
# FETCH DATA
# --------------------------------------------
@st.cache_data(ttl=300)
def load_data(symbol):
    df = yf.download(symbol, period="5d", interval="5m")
    df = df.dropna()
    return df

try:
    df = load_data(ticker)
except Exception as e:
    st.error(f"Failed to fetch data: {e}")
    st.stop()

st.write(f"Last updated: {df.index[-1]}")

# --------------------------------------------
# INDICATOR CALCULATIONS
# --------------------------------------------
df["RSI"] = RSIIndicator(df["Close"], window=14).rsi()
df["%K"] = StochasticOscillator(df["High"], df["Low"], df["Close"], window=14).stoch()
df["StochRSI"] = StochRSIIndicator(df["Close"], window=14).stochrsi()
df["MACD"] = MACD(df["Close"], window_slow=26, window_fast=12, window_sign=9).macd_diff()
adx = ADXIndicator(df["High"], df["Low"], df["Close"], window=14)
df["ADX"] = adx.adx()
df["DI+"] = adx.adx_pos()
df["DI-"] = adx.adx_neg()
df["Williams %R"] = WilliamsRIndicator(df["High"], df["Low"], df["Close"], lbp=14).williams_r()
df["CCI"] = CCIIndicator(df["High"], df["Low"], df["Close"], window=14).cci()
df["Ultimate Oscillator"] = UltimateOscillator(df["High"], df["Low"], df["Close"]).ultimate_oscillator()
df["ROC"] = ROCIndicator(df["Close"], window=12).roc()
df["Bull/Bear Power"] = df["Close"] - df["Close"].ewm(span=13).mean()

# --------------------------------------------
# SIGNAL LOGIC
# --------------------------------------------
latest = df.iloc[-1]

def get_signal(name, val):
    if name == "RSI":
        if val < 30: return "BUY"
        elif val > 70: return "SELL"
        else: return "NEUTRAL"

    elif name == "%K":
        if val < 20: return "BUY"
        elif val > 80: return "SELL"
        else: return "NEUTRAL"

    elif name == "StochRSI":
        if val < 0.2: return "BUY"
        elif val > 0.8: return "SELL"
        else: return "NEUTRAL"

    elif name == "MACD":
        if val > 0: return "BUY"
        elif val < 0: return "SELL"
        else: return "NEUTRAL"

    elif name == "ADX":
        if latest["ADX"] > 25:
            if latest["DI+"] > latest["DI-"]: return "BUY"
            elif latest["DI+"] < latest["DI-"]: return "SELL"
        return "NEUTRAL"

    elif name == "Williams %R":
        if val < -80: return "BUY"
        elif val > -20: return "SELL"
        else: return "NEUTRAL"

    elif name == "CCI":
        if val < -100: return "BUY"
        elif val > 100: return "SELL"
        else: return "NEUTRAL"

    elif name == "Ultimate Oscillator":
        if val < 30: return "BUY"
        elif val > 70: return "SELL"
        else: return "NEUTRAL"

    elif name == "ROC":
        if val > 0: return "BUY"
        elif val < 0: return "SELL"
        else: return "NEUTRAL"

    elif name == "Bull/Bear Power":
        if val > 0: return "BUY"
        elif val < 0: return "SELL"
        else: return "NEUTRAL"

# --------------------------------------------
# BUILD SIGNAL TABLE
# --------------------------------------------
signals = {
    "RSI (14)": [round(latest["RSI"], 2), get_signal("RSI", latest["RSI"])],
    "Stochastic (9,6)": [round(latest["%K"], 2), get_signal("%K", latest["%K"])],
    "Stochastic RSI (14)": [round(latest["StochRSI"], 2), get_signal("StochRSI", latest["StochRSI"])],
    "MACD (12,26)": [round(latest["MACD"], 2), get_signal("MACD", latest["MACD"])],
    "ADX (14)": [round(latest["ADX"], 2), get_signal("ADX", latest["ADX"])],
    "Williams %R": [round(latest["Williams %R"], 2), get_signal("Williams %R", latest["Williams %R"])],
    "CCI (14)": [round(latest["CCI"], 2), get_signal("CCI", latest["CCI"])],
    "Ultimate Oscillator": [round(latest["Ultimate Oscillator"], 2), get_signal("Ultimate Oscillator", latest["Ultimate Oscillator"])],
    "ROC": [round(latest["ROC"], 2), get_signal("ROC", latest["ROC"])],
    "Bull/Bear Power (13)": [round(latest["Bull/Bear Power"], 2), get_signal("Bull/Bear Power", latest["Bull/Bear Power"])],
}

signals_df = pd.DataFrame(signals, index=["Value", "Signal"]).T
st.dataframe(signals_df.style.highlight_max(axis=0, color="lightgreen").highlight_min(axis=0, color="#FFB6B6"))

# --------------------------------------------
# SUMMARY
# --------------------------------------------
buy = sum(1 for s in signals_df["Signal"] if s == "BUY")
sell = sum(1 for s in signals_df["Signal"] if s == "SELL")
neutral = sum(1 for s in signals_df["Signal"] if s == "NEUTRAL")

st.subheader("📈 Overall Summary")
col1, col2, col3 = st.columns(3)
col1.metric("BUY", buy)
col2.metric("SELL", sell)
col3.metric("NEUTRAL", neutral)

st.markdown("---")
st.caption("⚠️ This dashboard uses delayed Yahoo Finance data and is for educational use only.")
