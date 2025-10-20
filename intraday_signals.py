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
    df["SMA_20"] = ta.trend.SMAIndicator(df["Close"], window=20).sma_indicator()]()
