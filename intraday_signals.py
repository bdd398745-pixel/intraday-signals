import yfinance as yf
import pandas as pd
import streamlit as st
from ta.momentum import RSIIndicator, StochasticOscillator, StochRSIIndicator, ROCIndicator, UltimateOscillator
from ta.trend import MACD, ADXIndicator, CCIIndicator

# --- Streamlit Page Config ---
st.set_page_config(page_title="Intraday Signals", layout="wide")
st.title("Intraday Buy/Sell/Neutral Signals")

# --- Input ---
stocks_input = st.text_input(
    "Enter stock tickers (comma separated, NSE format e.g., TCS.NS, INFY.NS):"
)
interval = st.selectbox("Select interval", ["1m", "5m", "15m", "30m", "1h"])
period_options = {"1m": ["1d", "5d"], "5m": ["1d", "5d", "7d"], "15m": ["1d", "5d", "7d"],
                  "30m": ["1d", "5d", "7d"], "1h": ["1d", "5d", "7d"]}
period = st.selectbox("Select period", period_options[interval])

# --- Caching data fetching ---
@st.cache_data
def fetch_data(ticker, interval, period):
    df = yf.download(ticker, interval=interval, period=period)
    return df

# --- Highlighting function ---
def highlight_signal(val):
    if val == "BUY":
        color = "green"
    elif val == "SELL":
        color = "red"
    else:
        color = "yellow"
    return f'background-color: {color}'

if stocks_input:
    tickers = [s.strip() for s in stocks_input.split(",")]
    signals = []

    for ticker in tickers:
        df = fetch_data(ticker, interval, period)
        if df.empty:
            st.warning(f"No data for {ticker}")
            continue

        # --- Ensure columns are 1D Series ---
        close = df['Close']
        high = df['High']
        low = df['Low']
        if isinstance(close, pd.DataFrame): close = close.iloc[:, 0]
        if isinstance(high, pd.DataFrame): high = high.iloc[:, 0]
        if isinstance(low, pd.DataFrame): low = low.iloc[:, 0]
        df = pd.DataFrame({'Close': close, 'High': high, 'Low': low})

        # --- Indicators ---
        rsi = RSIIndicator(df['Close'], window=14).rsi()
        stoch = StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3).stoch()
        stoch_rsi = StochRSIIndicator(df['Close'], window=14, smooth1=3, smooth2=3).stochrsi()
        macd_val = MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9).macd_diff()
        adx_val = ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx()
        cci_val = CCIIndicator(df['High'], df['Low'], df['Close'], window=14).cci()
        ult_osc = UltimateOscillator(df['High'], df['Low'], df['Close'], window1=7, window2=14, window3=28).ultimate_oscillator()
        roc_val = ROCIndicator(df['Close'], window=12).roc()

        # --- Bull/Bear Power manually ---
        df['EMA13'] = df['Close'].ewm(span=13, adjust=False).mean()
        df['Bull/Bear'] = df['High'] - df['EMA13']

        # --- Williams %R ---
        will_r = (df['Close'] - df['High'].rolling(14).max()) / (
            df['High'].rolling(14).max() - df['Low'].rolling(14).min()
        ) * -100

        # --- Last values dictionary ---
        last = {
            'Stock': ticker,
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

        # --- Signal functions ---
        def signal_rsi(x): return "BUY" if x < 30 else "SELL" if x > 70 else "NEUTRAL"
        def signal_stoch(x): return "BUY" if x < 20 else "SELL" if x > 80 else "NEUTRAL"
        def signal_stochrsi(x): return "BUY" if x < 0.2 else "SELL" if x > 0.8 else "NEUTRAL"
        def signal_macd(x): return "BUY" if x > 0 else "SELL" if x < 0 else "NEUTRAL"
        def signal_adx(x): return "BUY" if x > 25 else "NEUTRAL"
        def signal_willr(x): return "BUY" if x < -80 else "SELL" if x > -20 else "NEUTRAL"
        def signal_cci(x): return "BUY" if x < -100 else "SELL" if x > 100 else "NEUTRAL"
        def signal_ultosc(x): return "BUY" if x < 30 else "SELL" if x > 70 else "NEUTRAL"
        def signal_roc(x): return "BUY" if x > 0 else "SELL" if x < 0 else "NEUTRAL"
        def signal_bb(x): return "BUY" if x > 0 else "SELL" if x < 0 else "NEUTRAL"

        last['RSI Signal'] = signal_rsi(last['RSI'])
        last['Stoch Signal'] = signal_stoch(last['Stoch'])
        last['Stoch RSI Signal'] = signal_stochrsi(last['Stoch RSI'])
        last['MACD Signal'] = signal_macd(last['MACD'])
        last['ADX Signal'] = signal_adx(last['ADX'])
        last['Williams %R Signal'] = signal_willr(last['Williams %R'])
        last['CCI Signal'] = signal_cci(last['CCI'])
        last['Ultimate Osc Signal'] = signal_ultosc(last['Ultimate Osc'])
        last['ROC Signal'] = signal_roc(last['ROC'])
        last['Bull/Bear Signal'] = signal_bb(last['Bull/Bear'])

        # --- Combined Signal ---
        scores = []
        for col in [
            'RSI Signal','Stoch Signal','Stoch RSI Signal','MACD Signal','ADX Signal',
            'Williams %R Signal','CCI Signal','Ultimate Osc Signal','ROC Signal','Bull/Bear Signal'
        ]:
            scores.append(1 if last[col]=="BUY" else -1 if last[col]=="SELL" else 0)
        total_score = sum(scores)
        last['Combined Signal'] = "BUY" if total_score>0 else "SELL" if total_score<0 else "NEUTRAL"

        signals.append(last)

    # --- Display Tables Separately ---
if signals:
    # Convert to DataFrame
    df_signals = pd.DataFrame(signals)
    
    # --- Indicator Values Table ---
    indicator_cols = ['Stock', 'RSI', 'Stoch', 'Stoch RSI', 'MACD', 'ADX', 
                      'Williams %R', 'CCI', 'Ultimate Osc', 'ROC', 'Bull/Bear']
    st.subheader("Indicator Values Table")
    st.dataframe(df_signals[indicator_cols].style.format("{:.2f}"))

    # --- Signal Table ---
    signal_cols = ['Stock', 'RSI Signal','Stoch Signal','Stoch RSI Signal','MACD Signal','ADX Signal',
                   'Williams %R Signal','CCI Signal','Ultimate Osc Signal','ROC Signal',
                   'Bull/Bear Signal','Combined Signal']
    st.subheader("Indicator Signals Table")
    st.dataframe(df_signals[signal_cols].style.applymap(
        highlight_signal, subset=signal_cols[1:]
    ))
