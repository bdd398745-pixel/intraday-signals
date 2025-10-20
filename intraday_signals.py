import yfinance as yf
import pandas as pd
import streamlit as st
from ta.momentum import RSIIndicator, StochasticOscillator, StochRSIIndicator, ROCIndicator, UltimateOscillator
from ta.trend import MACD, ADXIndicator, CCIIndicator

st.set_page_config(page_title="Intraday Signals", layout="wide")
st.title("Intraday Buy/Sell/Neutral Signals")

stocks_input = st.text_input(
    "Enter stock tickers (comma separated, NSE format e.g., TCS.NS, INFY.NS):"
)
interval = st.selectbox("Select interval", ["1m", "5m", "15m", "30m", "1h"])
period = st.selectbox("Select period", ["1d", "5d", "7d"])

def force_1d(series):
    """Ensure series is 1D numeric"""
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    return pd.to_numeric(series, errors='coerce')

if stocks_input:
    tickers = [s.strip() for s in stocks_input.split(",")]
    signals = []

    for ticker in tickers:
        df = yf.download(ticker, interval=interval, period=period, progress=False)
        if df.empty:
            st.warning(f"No data for {ticker}")
            continue

        # --- Force 1D numeric ---
        df['Close'] = force_1d(df['Close'])
        df['High'] = force_1d(df['High'])
        df['Low'] = force_1d(df['Low'])
        df = df[['Close', 'High', 'Low']].dropna()
        if df.empty:
            st.warning(f"No valid numeric data for {ticker}")
            continue

        # --- Indicators ---
        rsi = RSIIndicator(df['Close'], window=14).rsi()
        stoch = StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3).stoch()
        stoch_rsi = StochRSIIndicator(df['Close'], window=14, smooth1=3, smooth2=3).stochrsi()
        macd_val = MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9).macd_diff()
        adx_val = ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx()
        cci_val = CCIIndicator(df['High'], df['Low'], df['Close'], window=14).cci()
        ult_osc = UltimateOscillator(df['High'], df['Low'], df['Close'], window1=7, window2=14, window3=28).ultimate_oscillator()
        roc_val = ROCIndicator(df['Close'], window=12).roc()

        # --- Bull/Bear ---
        df['EMA13'] = df['Close'].ewm(span=13, adjust=False).mean()
        df['Bull/Bear'] = df['High'] - df['EMA13']

        # --- Williams %R ---
        will_r = (df['Close'] - df['High'].rolling(14).max()) / (
            df['High'].rolling(14).max() - df['Low'].rolling(14).min()
        ) * -100

        last = {
            'Stock': ticker,
            'Close': df['Close'].iloc[-1],
            'RSI': rsi.iloc[-1],
            'Stoch': stoch.iloc[-1],
            'Stoch RSI': stoch_rsi.iloc[-1],
            'MACD': macd_val.iloc[-1],
            'ADX': adx_val.iloc[-1],
            'Williams %R': will_r.iloc[-1],
            'CCI': cci_val.iloc[-1],
            'Ultimate Osc': ult_osc.iloc[-1],
            'ROC': roc_val.iloc[-1],
            'Bull/Bear': df['Bull/Bear'].iloc[-1]
        }

        # --- Signals ---
        def s_rsi(x): return "BUY" if x < 30 else "SELL" if x > 70 else "NEUTRAL"
        def s_stoch(x): return "BUY" if x < 20 else "SELL" if x > 80 else "NEUTRAL"
        def s_stochrsi(x): return "BUY" if x < 0.2 else "SELL" if x > 0.8 else "NEUTRAL"
        def s_macd(x): return "BUY" if x > 0 else "SELL" if x < 0 else "NEUTRAL"
        def s_adx(x): return "BUY" if x > 25 else "NEUTRAL"
        def s_willr(x): return "BUY" if x < -80 else "SELL" if x > -20 else "NEUTRAL"
        def s_cci(x): return "BUY" if x < -100 else "SELL" if x > 100 else "NEUTRAL"
        def s_ultosc(x): return "BUY" if x < 30 else "SELL" if x > 70 else "NEUTRAL"
        def s_roc(x): return "BUY" if x > 0 else "SELL" if x < 0 else "NEUTRAL"
        def s_bb(x): return "BUY" if x > 0 else "SELL" if x < 0 else "NEUTRAL"

        last['RSI Signal'] = s_rsi(last['RSI'])
        last['Stoch Signal'] = s_stoch(last['Stoch'])
        last['Stoch RSI Signal'] = s_stochrsi(last['Stoch RSI'])
        last['MACD Signal'] = s_macd(last['MACD'])
        last['ADX Signal'] = s_adx(last['ADX'])
        last['Williams %R Signal'] = s_willr(last['Williams %R'])
        last['CCI Signal'] = s_cci(last['CCI'])
        last['Ultimate Osc Signal'] = s_ultosc(last['Ultimate Osc'])
        last['ROC Signal'] = s_roc(last['ROC'])
        last['Bull/Bear Signal'] = s_bb(last['Bull/Bear'])

        # --- Combined ---
        scores = [1 if last[c]=="BUY" else -1 if last[c]=="SELL" else 0 for c in [
            'RSI Signal','Stoch Signal','Stoch RSI Signal','MACD Signal','ADX Signal',
            'Williams %R Signal','CCI Signal','Ultimate Osc Signal','ROC Signal','Bull/Bear Signal']]
        total_score = sum(scores)
        last['Combined Signal'] = "BUY" if total_score>0 else "SELL" if total_score<0 else "NEUTRAL"

        # --- Suggested Buy/Sell ---
        last['Suggested Buy'] = round(last['Close']*0.995,2)
        last['Suggested Sell'] = round(last['Close']*1.005,2)
        last['Buy Now?'] = "YES" if last['Close'] <= last['Suggested Buy'] else "NO"
        last['Sell Now?'] = "YES" if last['Close'] >= last['Suggested Sell'] else "NO"

        signals.append(last)

    st.dataframe(pd.DataFrame(signals))
