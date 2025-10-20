import yfinance as yf
import pandas as pd
import streamlit as st
from ta.momentum import RSIIndicator, StochasticOscillator, StochRSIIndicator
from ta.trend import MACD, ADXIndicator, CCIIndicator
from ta.volume import OnBalanceVolumeIndicator

st.set_page_config(page_title="Intraday Signals", layout="wide")
st.title("Intraday Buy/Sell Signals")

# --- Input ---
stocks_input = st.text_input(
    "Enter stock tickers (comma separated, NSE format e.g., TCS.NS, INFY.NS):"
)
interval = st.selectbox("Select interval", ["1m", "5m", "15m", "30m", "1h"])
period = st.selectbox("Select period", ["1d", "5d", "7d"])

def to_1d(series):
    """Ensure series is 1-dimensional"""
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    return pd.Series(series)

def get_signal(value, buy_thresh, sell_thresh, lower_is_buy=True):
    """Generic signal helper"""
    if lower_is_buy:
        return "BUY" if value < buy_thresh else "SELL" if value > sell_thresh else "NEUTRAL"
    else:
        return "BUY" if value > buy_thresh else "SELL" if value < sell_thresh else "NEUTRAL"

if stocks_input:
    tickers = [s.strip() for s in stocks_input.split(",")]
    signals_list = []

    for ticker in tickers:
        df = yf.download(ticker, interval=interval, period=period, progress=False)
        if df.empty:
            st.warning(f"No data for {ticker}")
            continue

        # --- Ensure 1D Series ---
        df['Close'] = to_1d(df['Close'])
        df['High'] = to_1d(df['High'])
        df['Low'] = to_1d(df['Low'])

        # --- Indicators ---
        rsi = RSIIndicator(df['Close'], window=14).rsi().iloc[-1]
        stoch = StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3).stoch().iloc[-1]
        stoch_rsi = StochRSIIndicator(df['Close'], window=14, smooth1=3, smooth2=3).stochrsi().iloc[-1]
        macd_val = MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9).macd_diff().iloc[-1]
        adx_val = ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx().iloc[-1]
        cci_val = CCIIndicator(df['High'], df['Low'], df['Close'], window=14).cci().iloc[-1]

        # --- Simple Combined Signal ---
        signals = {
            'Stock': ticker,
            'RSI Signal': get_signal(rsi, 30, 70),
            'Stoch Signal': get_signal(stoch, 20, 80),
            'Stoch RSI Signal': get_signal(stoch_rsi, 0.2, 0.8),
            'MACD Signal': get_signal(macd_val, 0, 0, lower_is_buy=False),
            'ADX Signal': "BUY" if adx_val > 25 else "NEUTRAL",
            'CCI Signal': get_signal(cci_val, -100, 100)
        }

        # Combined
        score = 0
        for s in ['RSI Signal', 'Stoch Signal', 'Stoch RSI Signal', 'MACD Signal', 'ADX Signal', 'CCI Signal']:
            if signals[s] == "BUY":
                score += 1
            elif signals[s] == "SELL":
                score -= 1
        signals['Combined Signal'] = "BUY" if score > 0 else "SELL" if score < 0 else "NEUTRAL"

        signals_list.append(signals)

    if signals_list:
        st.dataframe(pd.DataFrame(signals_list))
