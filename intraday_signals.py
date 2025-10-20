import yfinance as yf
import pandas as pd
import streamlit as st
from ta.momentum import RSIIndicator, StochasticOscillator, StochRSIIndicator, ROCIndicator, UltimateOscillator
from ta.trend import MACD, ADXIndicator, CCIIndicator

st.set_page_config(page_title="Intraday Signals", layout="wide")
st.title("Intraday Buy/Sell/Neutral Signals")

# --- Input ---
stocks_input = st.text_input(
    "Enter stock tickers (comma separated, NSE format e.g., TCS.NS, INFY.NS):"
)
interval = st.selectbox("Select interval", ["1m", "5m", "15m", "30m", "1h"])
period = st.selectbox("Select period", ["1d", "5d", "7d"])

if stocks_input:
    tickers = [s.strip() for s in stocks_input.split(",")]
    signals = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, interval=interval, period=period)
        except Exception as e:
            st.warning(f"Error fetching data for {ti
