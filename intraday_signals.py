import yfinance as yf
import pandas as pd
import streamlit as st
from ta.momentum import RSIIndicator, StochasticOscillator, StochRSIIndicator, ROCIndicator, UltimateOscillator
from ta.trend import MACD, ADXIndicator, CCIIndicator

st.set_page_config(page_title="Intraday Signals", layout="wide")
st.title("Intraday Buy/Sell Signals (1m-1h)")

# --- Input ---
stocks_input = st.text_input(
    "Enter stock tickers (comma separated, NSE format e.g., TCS.NS, INFY.NS):"
)
interval = st.selectbox("Select interval", ["1m", "5m", "15m", "30m", "1h"])
period = st.selectbox("Select period", ["1d", "5d", "7d"])

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
        df['Close'] = df['Close'].squeeze()
        df['High'] = df['High'].squeeze()
        df['Low'] = df['Low'].squeeze()

        # --- Indicators ---
        rsi = RSIIndicator(df['Close'], window=14).rsi().iloc[-1]
        stoch = StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3).stoch().iloc[-1]
        stoch_rsi = StochRSIIndicator(df['Close'], window=14, smooth1=3, smooth2=3).stochrsi().iloc[-1]
        macd_val = MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9).macd_diff().iloc[-1]
        adx_val = ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx().iloc[-1]
        cci_val = CCIIndicator(df['High'], df['Low'], df['Close'], window=14).cci().iloc[-1]
        ult_osc = UltimateOscillator(df['High'], df['Low'], df['Close'], window1=7, window2=14, window3=28).ultimate_oscillator().iloc[-1]
        roc_val = ROCIndicator(df['Close'], window=12).roc().iloc[-1]

        # --- Bull/Bear ---
        ema13 = df['Close'].ewm(span=13, adjust=False).mean()
        bull_bear = df['High'].iloc[-1] - ema13.iloc[-1]

        # --- Williams %R ---
        will_r = ((df['Close'].iloc[-1] - df['High'].rolling(14).max().iloc[-1]) /
                  (df['High'].rolling(14).max().iloc[-1] - df['Low'].rolling(14).min().iloc[-1])) * -100

        # --- Signals ---
        signal_data = {
            'Stock': ticker,
            'RSI': rsi,
            'RSI Signal': get_signal(rsi, 30, 70),
            'Stoch': stoch,
            'Stoch Signal': get_signal(stoch, 20, 80),
            'Stoch RSI': stoch_rsi,
            'Stoch RSI Signal': get_signal(stoch_rsi, 0.2, 0.8),
            'MACD': macd_val,
            'MACD Signal': get_signal(macd_val, 0, 0, lower_is_buy=False),
            'ADX': adx_val,
            'ADX Signal': "BUY" if adx_val > 25 else "NEUTRAL",
            'CCI': cci_val,
            'CCI Signal': get_signal(cci_val, -100, 100),
            'Ultimate Osc': ult_osc,
            'Ultimate Osc Signal': get_signal(ult_osc, 30, 70),
            'ROC': roc_val,
            'ROC Signal': get_signal(roc_val, 0, 0, lower_is_buy=False),
            'Bull/Bear': bull_bear,
            'Bull/Bear Signal': get_signal(bull_bear, 0, 0, lower_is_buy=False),
            'Williams %R': will_r,
            'Williams %R Signal': get_signal(will_r, -80, -20),
        }

        # --- Combined Signal ---
        score = 0
        for col in ['RSI Signal','Stoch Signal','Stoch RSI Signal','MACD Signal','ADX Signal',
                    'CCI Signal','Ultimate Osc Signal','ROC Signal','Bull/Bear Signal','Williams %R Signal']:
            if signal_data[col] == "BUY":
                score += 1
            elif signal_data[col] == "SELL":
                score -= 1
        signal_data['Combined Signal'] = "BUY" if score > 0 else "SELL" if score < 0 else "NEUTRAL"

        signals_list.append(signal_data)

    if signals_list:
        df_signals = pd.DataFrame(signals_list)
        st.dataframe(df_signals)
