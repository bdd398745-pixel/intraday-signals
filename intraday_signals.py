import yfinance as yf
import pandas as pd
import streamlit as st
from ta.momentum import RSIIndicator, StochasticOscillator, StochRSIIndicator, ROCIndicator, UltimateOscillator
from ta.trend import MACD, ADXIndicator, CCIIndicator

# --- Streamlit Page Config ---
st.set_page_config(page_title="📈 Intraday Signals", layout="wide")
st.title("🚀 Intraday Buy/Sell/Neutral Signals Dashboard")

# --- User Inputs ---
stocks_input = st.text_input(
    "Enter stock tickers (comma separated, NSE format e.g., TCS.NS, INFY.NS, or foreign like AAPL):"
)
interval = st.selectbox("Select interval", ["1m", "5m", "15m", "30m", "1h"])
period_options = {"1m": ["1d", "5d"], "5m": ["1d", "5d", "7d"], "15m": ["1d", "5d", "7d"],
                  "30m": ["1d", "5d", "7d"], "1h": ["1d", "5d", "7d"]}
period = st.selectbox("Select period", period_options[interval])

from streamlit_autorefresh import st_autorefresh

# --- Auto Refresh (Every 1 mins) ---
refresh = st.checkbox("🔄 Auto-refresh every 1 minutes", value=False)
if refresh:
    count = st_autorefresh(interval=1 * 60 * 1000, limit=None, key="datarefresh")
    st.info(f"⏳ Auto-refresh active — last refreshed {count} times.")


# --- Caching data fetching ---
@st.cache_data
def fetch_data(ticker, interval, period):
    df = yf.download(ticker, interval=interval, period=period, progress=False)

    # --- Fix yfinance 2D or MultiIndex issues ---
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = df[col].squeeze()

    df = df.dropna()
    return df


# --- Color highlight function for signal table ---
def highlight_signal(val):
    if val == "BUY":
        color = "lightgreen"
    elif val == "SELL":
        color = "salmon"
    else:
        color = "khaki"
    return f'background-color: {color}'


if stocks_input:
    tickers = [s.strip() for s in stocks_input.split(",")]
    value_rows = []
    signal_rows = []

    for ticker in tickers:
        df = fetch_data(ticker, interval, period)

        if df.empty:
            st.warning(f"⚠️ No data found for {ticker}")
            continue

        close = df['Close']
        high = df['High']
        low = df['Low']

        # --- Indicators ---
        rsi = RSIIndicator(close, window=9).rsi()
        stoch = StochasticOscillator(high, low, close, window=14, smooth_window=3).stoch()
        stoch_rsi = StochRSIIndicator(close, window=14, smooth1=3, smooth2=3).stochrsi()
        macd_val = MACD(close, window_slow=26, window_fast=12, window_sign=9).macd_diff()
        adx_val = ADXIndicator(high, low, close, window=14).adx()
        cci_val = CCIIndicator(high, low, close, window=14).cci()
        ult_osc = UltimateOscillator(high, low, close, window1=7, window2=14, window3=28).ultimate_oscillator()
        roc_val = ROCIndicator(close, window=12).roc()

        df['EMA13'] = close.ewm(span=13, adjust=False).mean()
        df['Bull/Bear'] = high - df['EMA13']

        will_r = (close - high.rolling(14).max()) / (
            high.rolling(14).max() - low.rolling(14).min()
        ) * -100

        # --- Last values ---
        last = {
            'Stock': ticker,
            'LTP': round(close.iloc[-1], 2),
            'RSI': round(rsi.iloc[-1], 2),
            'Stoch': round(stoch.iloc[-1], 2),
            'Stoch RSI': round(stoch_rsi.iloc[-1], 2),
            'MACD': round(macd_val.iloc[-1], 4),
            'ADX': round(adx_val.iloc[-1], 2),
            'Williams %R': round(will_r.iloc[-1], 2),
            'CCI': round(cci_val.iloc[-1], 2),
            'Ultimate Osc': round(ult_osc.iloc[-1], 2),
            'ROC': round(roc_val.iloc[-1], 2),
            'Bull/Bear': round(df['Bull/Bear'].iloc[-1], 2)
        }

        # --- Signal Logic ---
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

        # --- Apply signal rules ---
        signals = {
            'Stock': ticker,
            'RSI Signal': signal_rsi(last['RSI']),
            'Stoch Signal': signal_stoch(last['Stoch']),
            'Stoch RSI Signal': signal_stochrsi(last['Stoch RSI']),
            'MACD Signal': signal_macd(last['MACD']),
            'ADX Signal': signal_adx(last['ADX']),
            'Williams %R Signal': signal_willr(last['Williams %R']),
            'CCI Signal': signal_cci(last['CCI']),
            'Ultimate Osc Signal': signal_ultosc(last['Ultimate Osc']),
            'ROC Signal': signal_roc(last['ROC']),
            'Bull/Bear Signal': signal_bb(last['Bull/Bear'])
        }

        # --- Combined Signal ---
        score_map = {"BUY": 1, "SELL": -1, "NEUTRAL": 0}
        total_score = sum(score_map[v] for v in signals.values() if v in score_map)
        signals['Combined Signal'] = "BUY" if total_score > 0 else "SELL" if total_score < 0 else "NEUTRAL"

        value_rows.append(last)
        signal_rows.append(signals)

    # --- Create DataFrames ---
    df_values = pd.DataFrame(value_rows)
    df_signals = pd.DataFrame(signal_rows)

    # --- Display ---
    st.subheader("📊 Indicator Values Table")
    st.dataframe(df_values, use_container_width=True)

    st.subheader("📈 Trading Signals Table")
    st.dataframe(
        df_signals.style.applymap(
            highlight_signal,
            subset=['RSI Signal', 'Stoch Signal', 'Stoch RSI Signal', 'MACD Signal', 'ADX Signal',
                    'Williams %R Signal', 'CCI Signal', 'Ultimate Osc Signal', 'ROC Signal',
                    'Bull/Bear Signal', 'Combined Signal']
        ),
        use_container_width=True
    )
