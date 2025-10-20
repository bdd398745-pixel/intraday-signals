import yfinance as yf
import pandas as pd
import streamlit as st
from ta.volatility import AverageTrueRange
from ta.momentum import RSIIndicator, StochasticOscillator, ROCIndicator
from ta.trend import MACD, ADXIndicator, CCIIndicator
from ta.others import UltimateOscillator, WilliamsRIndicator

st.set_page_config(page_title="Intraday Signal App", layout="wide")

st.title("📈 Intraday Signal App with Buy/Sell/Stoploss Prediction")

# --- Sidebar inputs ---
ticker = st.text_input("Enter Stock Symbol (e.g., TCS.NS, AAPL)", "TCS.NS")
interval = st.selectbox("Select Interval", ["1m", "5m", "15m", "30m", "1h"])
period = st.selectbox("Select Period", ["1d", "5d", "1mo"])

# --- Fetch data ---
try:
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    df.dropna(inplace=True)
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

# --- Indicator Calculations ---
df["RSI"] = RSIIndicator(df["Close"], window=14).rsi()
stoch = StochasticOscillator(df["High"], df["Low"], df["Close"], window=14, smooth_window=3)
df["Stoch_K"] = stoch.stoch()
macd = MACD(df["Close"], window_slow=26, window_fast=12, window_sign=9)
df["MACD"] = macd.macd()
df["ADX"] = ADXIndicator(df["High"], df["Low"], df["Close"], window=14).adx()
df["CCI"] = CCIIndicator(df["High"], df["Low"], df["Close"], window=14).cci()
df["ROC"] = ROCIndicator(df["Close"], window=12).roc()
df["UO"] = UltimateOscillator(df["High"], df["Low"], df["Close"], 7, 14, 28).ultimate_oscillator()
df["WilliamsR"] = WilliamsRIndicator(df["High"], df["Low"], df["Close"], lbp=14).williams_r()
df["ATR"] = AverageTrueRange(df["High"], df["Low"], df["Close"], window=14).average_true_range()

# --- Signal Logic ---
df["RSI Signal"] = df["RSI"].apply(lambda x: "BUY" if x < 30 else "SELL" if x > 70 else "HOLD")
df["Stoch Signal"] = df["Stoch_K"].apply(lambda x: "BUY" if x < 20 else "SELL" if x > 80 else "HOLD")
df["MACD Signal"] = df["MACD"].diff().apply(lambda x: "BUY" if x > 0 else "SELL")
df["ADX Signal"] = df["ADX"].apply(lambda x: "BUY" if x > 25 else "HOLD")
df["CCI Signal"] = df["CCI"].apply(lambda x: "BUY" if x < -100 else "SELL" if x > 100 else "HOLD")
df["ROC Signal"] = df["ROC"].apply(lambda x: "BUY" if x > 0 else "SELL")
df["UO Signal"] = df["UO"].apply(lambda x: "BUY" if x < 30 else "SELL" if x > 70 else "HOLD")
df["WilliamsR Signal"] = df["WilliamsR"].apply(lambda x: "BUY" if x < -80 else "SELL" if x > -20 else "HOLD")

# --- Combine signals ---
df["Buy Count"] = df[["RSI Signal", "Stoch Signal", "MACD Signal", "ADX Signal", 
                      "CCI Signal", "ROC Signal", "UO Signal", "WilliamsR Signal"]].apply(lambda x: (x == "BUY").sum(), axis=1)
df["Sell Count"] = df[["RSI Signal", "Stoch Signal", "MACD Signal", "ADX Signal", 
                       "CCI Signal", "ROC Signal", "UO Signal", "WilliamsR Signal"]].apply(lambda x: (x == "SELL").sum(), axis=1)

def combined_signal(row):
    if row["Buy Count"] >= 5:
        return "BUY"
    elif row["Sell Count"] >= 5:
        return "SELL"
    else:
        return "HOLD"

df["Combined Signal"] = df.apply(combined_signal, axis=1)

# --- Price Prediction Logic ---
df["Buy Price"] = None
df["Sell Price"] = None
df["Stop Loss"] = None

for i in range(len(df)):
    ltp = df["Close"].iloc[i]
    atr = df["ATR"].iloc[i]
    signal = df["Combined Signal"].iloc[i]
    if signal == "BUY":
        df.at[i, "Buy Price"] = round(ltp * 1.002, 2)
        df.at[i, "Stop Loss"] = round(ltp - atr, 2)
    elif signal == "SELL":
        df.at[i, "Sell Price"] = round(ltp * 0.998, 2)
        df.at[i, "Stop Loss"] = round(ltp + atr, 2)

# --- Display ---
st.subheader("📊 Intraday Signal Table with Price Prediction")
st.dataframe(
    df[["Close", "RSI Signal", "Stoch Signal", "MACD Signal", "ADX Signal", 
        "CCI Signal", "ROC Signal", "UO Signal", "WilliamsR Signal", 
        "Combined Signal", "Buy Price", "Sell Price", "Stop Loss"]].tail(20),
    use_container_width=True
)
