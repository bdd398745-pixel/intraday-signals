import streamlit as st
import pandas as pd
import yfinance as yf
import ta
import time

# --------------------------------------------
# STREAMLIT PAGE SETUP
# --------------------------------------------
st.set_page_config(page_title="📊 Intraday Indicator Signals", layout="wide")
st.title("📊 Intraday Technical Signal Dashboard (Live Auto Refresh)")
st.caption("Data updates every few minutes from Yahoo Finance (5–10 min delay).")

# --------------------------------------------
# INPUT SECTION
# --------------------------------------------
symbol = st.text_input("Enter Stock Symbol (e.g., RELIANCE.NS)", "RELIANCE.NS")
interval = st.selectbox("Select Interval", ["1m", "5m", "15m", "30m", "1h", "1d"])
refresh_rate = st.slider("Auto Refresh (seconds)", 30, 300, 120)

# --------------------------------------------
# FETCH LIVE DATA
# --------------------------------------------
@st.cache_data(ttl=refresh_rate)
def get_data(symbol, interval):
    data = yf.download(tickers=symbol, period="5d", interval=interval)
    data.dropna(inplace=True)
    return data

try:
    df = get_data(symbol, interval)
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

# --------------------------------------------
# INDICATOR CALCULATIONS
# --------------------------------------------
df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
stoch = ta.momentum.StochasticOscillator(df["High"], df["Low"], df["Close"])
df["Stochastic"] = stoch.stoch()
df["Stochastic_RSI"] = ta.momentum.StochRSIIndicator(df["Close"]).stochrsi()
macd = ta.trend.MACD(df["Close"])
df["MACD"] = macd.macd()
df["MACD_signal"] = macd.macd_signal()
adx = ta.trend.ADXIndicator(df["High"], df["Low"], df["Close"])
df["ADX"] = adx.adx()
df["DI+"] = adx.adx_pos()
df["DI-"] = adx.adx_neg()
df["Williams %R"] = ta.momentum.WilliamsRIndicator(df["High"], df["Low"], df["Close"]).williams_r()
df["CCI"] = ta.trend.CCIIndicator(df["High"], df["Low"], df["Close"]).cci()
df["ROC"] = ta.momentum.ROCIndicator(df["Close"]).roc()
df["BullBearPower"] = df["High"] - ta.trend.EMAIndicator(df["Close"], 13).ema_indicator()

# Manual Ultimate Oscillator
df["BP"] = df["Close"] - df["Low"]
df["TR"] = df[["High", "Close"]].max(axis=1) - df[["Low", "Close"]].min(axis=1)
avg7 = df["BP"].rolling(7).sum() / df["TR"].rolling(7).sum()
avg14 = df["BP"].rolling(14).sum() / df["TR"].rolling(14).sum()
avg28 = df["BP"].rolling(28).sum() / df["TR"].rolling(28).sum()
df["UltimateOscillator"] = 100 * ((4 * avg7) + (2 * avg14) + avg28) / (4 + 2 + 1)

# --------------------------------------------
# SIGNAL GENERATION
# --------------------------------------------
latest = df.iloc[-1]
signals = {}

# RSI
if latest["RSI"] < 30:
    signals["RSI"] = "BUY"
elif latest["RSI"] > 70:
    signals["RSI"] = "SELL"
else:
    signals["RSI"] = "NEUTRAL"

# Stochastic
if latest["Stochastic"] < 20:
    signals["Stochastic"] = "BUY"
elif latest["Stochastic"] > 80:
    signals["Stochastic"] = "SELL"
else:
    signals["Stochastic"] = "NEUTRAL"

# Stoch RSI
if latest["Stochastic_RSI"] < 0.2:
    signals["Stochastic RSI"] = "BUY"
elif latest["Stochastic_RSI"] > 0.8:
    signals["Stochastic RSI"] = "SELL"
else:
    signals["Stochastic RSI"] = "NEUTRAL"

# MACD
if latest["MACD"] > latest["MACD_signal"]:
    signals["MACD"] = "BUY"
elif latest["MACD"] < latest["MACD_signal"]:
    signals["MACD"] = "SELL"
else:
    signals["MACD"] = "NEUTRAL"

# ADX
if latest["ADX"] > 25 and latest["DI+"] > latest["DI-"]:
    signals["ADX"] = "BUY"
elif latest["ADX"] > 25 and latest["DI-"] > latest["DI+"]:
    signals["ADX"] = "SELL"
else:
    signals["ADX"] = "NEUTRAL"

# Williams %R
if latest["Williams %R"] < -80:
    signals["Williams %R"] = "BUY"
elif latest["Williams %R"] > -20:
    signals["Williams %R"] = "SELL"
else:
    signals["Williams %R"] = "NEUTRAL"

# CCI
if latest["CCI"] < -100:
    signals["CCI"] = "BUY"
elif latest["CCI"] > 100:
    signals["CCI"] = "SELL"
else:
    signals["CCI"] = "NEUTRAL"

# Ultimate Oscillator
if latest["UltimateOscillator"] < 30:
    signals["Ultimate Oscillator"] = "BUY"
elif latest["UltimateOscillator"] > 70:
    signals["Ultimate Oscillator"] = "SELL"
else:
    signals["Ultimate Oscillator"] = "NEUTRAL"

# ROC
signals["ROC"] = "BUY" if latest["ROC"] > 0 else ("SELL" if latest["ROC"] < 0 else "NEUTRAL")

# Bull/Bear Power
signals["Bull/Bear Power"] = "BUY" if latest["BullBearPower"] > 0 else ("SELL" if latest["BullBearPower"] < 0 else "NEUTRAL")

# --------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------
signal_df = pd.DataFrame(signals.items(), columns=["Indicator", "Signal"])
st.dataframe(signal_df, use_container_width=True)

# --------------------------------------------
# AUTO REFRESH
# --------------------------------------------
time.sleep(refresh_rate)
st.experimental_rerun()
