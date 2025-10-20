import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# --------------------------------------------
# PAGE CONFIG
# --------------------------------------------
st.set_page_config(page_title="Intraday Stock Signals", layout="wide")
st.title("📊 Intraday Buy/Sell Signal Dashboard")
st.markdown("This tool gives real-time BUY/SELL signals using technical indicators (RSI, MACD, Stochastic RSI).")

# --------------------------------------------
# USER INPUTS
# --------------------------------------------
symbols_input = st.text_input("Enter stock symbols (comma-separated):", "RELIANCE.NS, TCS.NS, HDFCBANK.NS")
interval = st.selectbox("Select Time Interval", ["1m", "5m", "15m", "30m", "1h", "1d"], index=2)

symbols = [s.strip().upper() for s in symbols_input.split(",")]

# --------------------------------------------
# DATA FETCH FUNCTION
# --------------------------------------------
def get_data(symbol):
    data = yf.download(symbol, period="5d", interval=interval, progress=False)

    # Handle tuple output from yfinance
    if isinstance(data, tuple):
        data = data[0]

    # Safety check
    if data is None or data.empty:
        raise ValueError(f"No data fetched for {symbol}")

    data = data.reset_index()
    data.columns = [str(col).replace(" ", "_") for col in data.columns]

    # Ensure proper types
    for col in ["Open", "High", "Low", "Close"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data.dropna(inplace=True)
    return data

# --------------------------------------------
# INDICATOR CALCULATIONS
# --------------------------------------------
def compute_indicators(df):
    df["RSI"] = ta.momentum.RSIIndicator(close=df["Close"], window=14).rsi()
    macd = ta.trend.MACD(close=df["Close"])
    df["MACD"] = macd.macd()
    df["Signal_Line"] = macd.macd_signal()
    stoch = ta.momentum.StochasticOscillator(high=df["High"], low=df["Low"], close=df["Close"])
    df["Stochastic"] = stoch.stoch()
    df["Stochastic_Signal"] = stoch.stoch_signal()
    return df

# --------------------------------------------
# SIGNAL LOGIC
# --------------------------------------------
def get_signal(row):
    signals = {}

    # RSI
    if row["RSI"] < 30:
        signals["RSI"] = "BUY"
    elif row["RSI"] > 70:
        signals["RSI"] = "SELL"
    else:
        signals["RSI"] = "NEUTRAL"

    # MACD
    if row["MACD"] > row["Signal_Line"]:
        signals["MACD"] = "BUY"
    elif row["MACD"] < row["Signal_Line"]:
        signals["MACD"] = "SELL"
    else:
        signals["MACD"] = "NEUTRAL"

    # Stochastic
    if row["Stochastic"] < 20:
        signals["Stochastic"] = "BUY"
    elif row["Stochastic"] > 80:
        signals["Stochastic"] = "SELL"
    else:
        signals["Stochastic"] = "NEUTRAL"

    # Final Consensus
    buy_count = list(signals.values()).count("BUY")
    sell_count = list(signals.values()).count("SELL")

    if buy_count > sell_count:
        signals["Final_Signal"] = "🟢 STRONG BUY"
    elif sell_count > buy_count:
        signals["Final_Signal"] = "🔴 STRONG SELL"
    else:
        signals["Final_Signal"] = "⚪ HOLD"

    return signals

# --------------------------------------------
# MAIN SIGNAL GENERATION
# --------------------------------------------
st.subheader("📈 Live Stock Signals")

results = []
for symbol in symbols:
    try:
        df = get_data(symbol)
        df = compute_indicators(df)
        last = df.iloc[-1]
        signal = get_signal(last)
        results.append({
            "Symbol": symbol,
            "RSI": round(last["RSI"], 2),
            "MACD": round(last["MACD"], 2),
            "Stochastic": round(last["Stochastic"], 2),
            "Final Signal": signal["Final_Signal"]
        })
    except Exception as e:
        st.error(f"⚠️ Error for {symbol}: {e}")

# --------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------
if results:
    st.dataframe(pd.DataFrame(results), use_container_width=True)
else:
    st.warning("No valid data found for the given symbols.")

st.caption("⚡ Signals refresh when you rerun the app manually (Ctrl+R). Auto-refresh can be added later.")
