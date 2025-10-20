import yfinance as yf
import pandas as pd
import streamlit as st
from ta.momentum import RSIIndicator, StochasticOscillator, StochRSIIndicator, ROCIndicator
from ta.trend import MACD, ADXIndicator, CCIIndicator
import plotly.graph_objects as go

# --- Streamlit Page Config ---
st.set_page_config(page_title="Intraday Trading Assistant", layout="wide")
st.title("📈 Intraday Trading Assistant – Buy/Sell/Neutral Screener")

# --- Auto Refresh (Every 5 mins) ---
st_autorefresh = st.checkbox("🔄 Auto-refresh every 5 minutes", value=True)
if st_autorefresh:
    st.experimental_rerun = st.experimental_rerun  # ensures rerun defined
    st_autorefresh_interval = st.experimental_rerun  # for safety
    st_autorefresh = st_autorefresh

st.caption("Updated every 5 minutes when enabled")

# --- Inputs ---
stocks_input = st.text_input(
    "Enter stock tickers (comma separated, NSE format e.g., TCS.NS, INFY.NS):"
)
interval = st.selectbox("Select interval", ["1m", "5m", "15m", "30m"])
period_options = {"1m": ["1d", "5d"], "5m": ["1d", "5d", "7d"], "15m": ["1d", "5d", "7d"], "30m": ["1d", "5d", "7d"]}
period = st.selectbox("Select period", period_options[interval])

# --- Cache Data ---
@st.cache_data
def fetch_data(ticker, interval, period):
    return yf.download(ticker, interval=interval, period=period, progress=False)

# --- Highlight Function ---
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
    values_data, signals_data = [], []

    for ticker in tickers:
        df = fetch_data(ticker, interval, period)
        if df.empty:
            st.warning(f"No data for {ticker}")
            continue

        close, high, low, volume = df['Close'], df['High'], df['Low'], df['Volume']
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['Vol_SMA20'] = df['Volume'].rolling(20).mean()

        # Indicators
        rsi = RSIIndicator(df['Close'], window=9).rsi()  # faster RSI for intraday
        stoch = StochasticOscillator(df['High'], df['Low'], df['Close']).stoch()
        macd_val = MACD(df['Close']).macd_diff()
        adx_val = ADXIndicator(df['High'], df['Low'], df['Close']).adx()
        roc_val = ROCIndicator(df['Close'], window=9).roc()
        cci_val = CCIIndicator(df['High'], df['Low'], df['Close'], window=14).cci()

        # --- Last Values ---
        last = {
            "Stock": ticker,
            "LTP": close.iloc[-1],
            "RSI": rsi.iloc[-1],
            "Stoch": stoch.iloc[-1],
            "MACD": macd_val.iloc[-1],
            "ADX": adx_val.iloc[-1],
            "ROC": roc_val.iloc[-1],
            "CCI": cci_val.iloc[-1],
            "EMA9": df["EMA9"].iloc[-1],
            "EMA21": df["EMA21"].iloc[-1],
            "Volume": volume.iloc[-1],
            "Vol SMA(20)": df["Vol_SMA20"].iloc[-1],
        }

        # --- Signal Logic ---
        def signal_rsi(x): return "BUY" if x < 30 else "SELL" if x > 70 else "NEUTRAL"
        def signal_macd(x): return "BUY" if x > 0 else "SELL" if x < 0 else "NEUTRAL"
        def signal_adx(x): return "BUY" if x > 25 else "NEUTRAL"
        def signal_roc(x): return "BUY" if x > 0 else "SELL"
        def signal_cci(x): return "BUY" if x < -100 else "SELL" if x > 100 else "NEUTRAL"
        def signal_ema(): return "BUY" if df["EMA9"].iloc[-1] > df["EMA21"].iloc[-1] else "SELL"
        def signal_vol(): return "BUY" if volume.iloc[-1] > df["Vol_SMA20"].iloc[-1] else "NEUTRAL"

        signals = {
            "Stock": ticker,
            "LTP": close.iloc[-1],
            "RSI Signal": signal_rsi(last["RSI"]),
            "MACD Signal": signal_macd(last["MACD"]),
            "ADX Signal": signal_adx(last["ADX"]),
            "ROC Signal": signal_roc(last["ROC"]),
            "CCI Signal": signal_cci(last["CCI"]),
            "EMA Crossover": signal_ema(),
            "Volume Signal": signal_vol(),
        }

        # --- Combined Signal ---
        scores = []
        for col in ["RSI Signal", "MACD Signal", "ADX Signal", "ROC Signal", "CCI Signal", "EMA Crossover", "Volume Signal"]:
            scores.append(1 if signals[col] == "BUY" else -1 if signals[col] == "SELL" else 0)
        total_score = sum(scores)
        signals["Combined Signal"] = "BUY" if total_score >= 3 else "SELL" if total_score <= -3 else "NEUTRAL"

        values_data.append(last)
        signals_data.append(signals)

        # --- Chart (Candlestick + EMA9/21) ---
        st.subheader(f"📊 {ticker} Chart")
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Candles'
        )])
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA9'], line=dict(color='blue', width=1), name='EMA9'))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA21'], line=dict(color='red', width=1), name='EMA21'))
        st.plotly_chart(fig, use_container_width=True)

    # --- Display Tables ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📘 Indicator Values Table")
        st.dataframe(pd.DataFrame(values_data))
    with col2:
        st.subheader("📗 Signals Table")
        df_signals = pd.DataFrame(signals_data)
        st.dataframe(df_signals.style.applymap(
            highlight_signal,
            subset=["RSI Signal", "MACD Signal", "ADX Signal", "ROC Signal", "CCI Signal", "EMA Crossover", "Volume Signal", "Combined Signal"]
        ))

    # --- Quick Summary ---
    st.markdown("### 🔎 Summary")
    buy_stocks = [x["Stock"] for x in signals_data if x["Combined Signal"] == "BUY"]
    sell_stocks = [x["Stock"] for x in signals_data if x["Combined Signal"] == "SELL"]

    st.success(f"✅ BUY Signals: {', '.join(buy_stocks) if buy_stocks else 'None'}")
    st.error(f"❌ SELL Signals: {', '.join(sell_stocks) if sell_stocks else 'None'}")
