import yfinance as yf
import pandas as pd
import streamlit as st
from ta.volatility import AverageTrueRange
from ta.momentum import RSIIndicator, StochasticOscillator, ROCIndicator, WilliamsRIndicator
from ta.trend import MACD, ADXIndicator, CCIIndicator
from streamlit_autorefresh import st_autorefresh

# --- Streamlit Page Config ---
st.set_page_config(page_title="📈 Intraday Signals", layout="wide")
st.title("🚀 Intraday Buy/Sell/Stoploss Signal Dashboard")

# --- User Inputs ---
ticker_input = st.text_input(
    "Enter stock tickers (comma separated, NSE format e.g., TCS.NS, INFY.NS, or foreign like AAPL):"
)
interval = st.selectbox("Select interval", ["1m", "5m", "15m", "30m", "1h"])
period_options = {"1m": ["1d", "5d"], "5m": ["1d", "5d", "7d"], "15m": ["1d", "5d", "7d"],
                  "30m": ["1d", "5d", "7d"], "1h": ["1d", "5d", "7d"]}
period = st.selectbox("Select period", period_options[interval])

# --- Auto Refresh Option ---
refresh = st.checkbox("🔄 Auto-refresh every 1 minute", value=False)
if refresh:
    count = st_autorefresh(interval=60 * 1000, limit=None, key="datarefresh")
    st.info(f"⏳ Auto-refresh active — refreshed {count} times.")

# --- Cache Data ---
@st.cache_data
def fetch_data(ticker, interval, period):
    df = yf.download(ticker, interval=interval, period=period, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    df = df.dropna()
    return df


# --- Highlighting Function ---
def highlight_signal(val):
    if val == "BUY":
        color = "lightgreen"
    elif val == "SELL":
        color = "salmon"
    elif val == "HOLD":
        color = "khaki"
    else:
        color = "white"
    return f"background-color: {color}"


if ticker_input:
    tickers = [t.strip() for t in ticker_input.split(",")]
    signal_data = []

    for ticker in tickers:
        try:
            df = fetch_data(ticker, interval, period)
            if df.empty:
                st.warning(f"⚠️ No data for {ticker}")
                continue

            # --- Indicators ---
            df["RSI"] = RSIIndicator(df["Close"], window=14).rsi()
            stoch = StochasticOscillator(df["High"], df["Low"], df["Close"], window=14, smooth_window=3)
            df["Stoch_K"] = stoch.stoch()
            df["MACD"] = MACD(df["Close"], window_slow=26, window_fast=12, window_sign=9).macd()
            df["ADX"] = ADXIndicator(df["High"], df["Low"], df["Close"], window=14).adx()
            df["CCI"] = CCIIndicator(df["High"], df["Low"], df["Close"], window=14).cci()
            df["ROC"] = ROCIndicator(df["Close"], window=12).roc()
            df["WilliamsR"] = WilliamsRIndicator(df["High"], df["Low"], df["Close"], lbp=14).williams_r()
            df["ATR"] = AverageTrueRange(df["High"], df["Low"], df["Close"], window=14).average_true_range()

            # --- Signals ---
            df["RSI Signal"] = df["RSI"].apply(lambda x: "BUY" if x < 30 else "SELL" if x > 70 else "HOLD")
            df["Stoch Signal"] = df["Stoch_K"].apply(lambda x: "BUY" if x < 20 else "SELL" if x > 80 else "HOLD")
            df["MACD Signal"] = df["MACD"].diff().apply(lambda x: "BUY" if x > 0 else "SELL")
            df["ADX Signal"] = df["ADX"].apply(lambda x: "BUY" if x > 25 else "HOLD")
            df["CCI Signal"] = df["CCI"].apply(lambda x: "BUY" if x < -100 else "SELL" if x > 100 else "HOLD")
            df["ROC Signal"] = df["ROC"].apply(lambda x: "BUY" if x > 0 else "SELL")
            df["WilliamsR Signal"] = df["WilliamsR"].apply(lambda x: "BUY" if x < -80 else "SELL" if x > -20 else "HOLD")

            # --- Combine Signals ---
            df["Buy Count"] = df[["RSI Signal", "Stoch Signal", "MACD Signal", "ADX Signal",
                                  "CCI Signal", "ROC Signal", "WilliamsR Signal"]].apply(lambda x: (x == "BUY").sum(), axis=1)
            df["Sell Count"] = df[["RSI Signal", "Stoch Signal", "MACD Signal", "ADX Signal",
                                   "CCI Signal", "ROC Signal", "WilliamsR Signal"]].apply(lambda x: (x == "SELL").sum(), axis=1)

            def combined_signal(row):
                if row["Buy Count"] >= 4:
                    return "BUY"
                elif row["Sell Count"] >= 4:
                    return "SELL"
                else:
                    return "HOLD"

            df["Combined Signal"] = df.apply(combined_signal, axis=1)

            # --- Buy/Sell/Stoploss Prediction ---
            df["Buy Price"], df["Sell Price"], df["Stop Loss"] = None, None, None
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

            last = df.iloc[-1]
            signal_data.append({
                "Stock": ticker,
                "LTP": round(last["Close"], 2),
                "Combined Signal": last["Combined Signal"],
                "Buy Price": last["Buy Price"],
                "Sell Price": last["Sell Price"],
                "Stop Loss": last["Stop Loss"],
                "RSI": round(last["RSI"], 2),
                "Stoch": round(last["Stoch_K"], 2),
                "MACD": round(last["MACD"], 2),
                "ADX": round(last["ADX"], 2),
                "CCI": round(last["CCI"], 2),
                "ROC": round(last["ROC"], 2),
                "WilliamsR": round(last["WilliamsR"], 2),
            })

        except Exception as e:
            st.error(f"❌ Error for {ticker}: {e}")

    # --- Final Table ---
    if signal_data:
        df_final = pd.DataFrame(signal_data)
        st.subheader("📊 Intraday Signals with Buy/Sell/Stoploss")
        st.dataframe(
            df_final.style.applymap(highlight_signal, subset=["Combined Signal"]),
            use_container_width=True
        )
