import yfinance as yf
import pandas as pd
import streamlit as st
from ta.momentum import RSIIndicator, StochasticOscillator, StochRSIIndicator, ROCIndicator, UltimateOscillator
from ta.trend import MACD, ADXIndicator, CCIIndicator

# --- Streamlit Page Config ---
st.set_page_config(page_title="Intraday Signals", layout="wide")
st.title("Intraday Buy/Sell/Neutral Signals")

# --- Input ---
stocks_input = st.text_input("Enter stock tickers (comma separated, NSE format e.g., TCS.NS, INFY.NS):")
interval = st.selectbox("Select interval", ["1m", "5m", "15m", "30m", "1h"])
period_options = {"1m": ["1d", "5d"], "5m": ["1d", "5d", "7d"], "15m": ["1d", "5d", "7d"],
                  "30m": ["1d", "5d", "7d"], "1h": ["1d", "5d", "7d"]}
period = st.selectbox("Select period", period_options[interval])

# --- Function to fetch data ---
def fetch_data(ticker, interval, period):
    df = yf.download(ticker, interval=interval, period=period)
    return df

# --- Highlighting function ---
def highlight_signal(val):
    if val == "BUY":
        return 'background-color: green'
    elif val == "SELL":
        return 'background-color: red'
    else:
        return 'background-color: yellow'

# --- Main processing ---
if stocks_input:
    tickers = [t.strip() for t in stocks_input.split(",")]
    values_list = []
    signals_list = []

    for ticker in tickers:
        df = fetch_data(ticker, interval, period)
        if df.empty:
            st.warning(f"No data found for {ticker}")
            continue

        close = df['Close']
        high = df['High']
        low = df['Low']
        df = pd.DataFrame({'Close': close, 'High': high, 'Low': low})

        # --- Indicators ---
        rsi = RSIIndicator(df['Close']).rsi()
        stoch = StochasticOscillator(df['High'], df['Low'], df['Close']).stoch()
        stoch_rsi = StochRSIIndicator(df['Close']).stochrsi()
        macd_val = MACD(df['Close']).macd_diff()
        adx_val = ADXIndicator(df['High'], df['Low'], df['Close']).adx()
        cci_val = CCIIndicator(df['High'], df['Low'], df['Close']).cci()
        ult_osc = UltimateOscillator(df['High'], df['Low'], df['Close']).ultimate_oscillator()
        roc_val = ROCIndicator(df['Close']).roc()
        df['EMA13'] = df['Close'].ewm(span=13, adjust=False).mean()
        bull_bear = df['High'] - df['EMA13']
        will_r = (df['Close'] - df['High'].rolling(14).max()) / (df['High'].rolling(14).max() - df['Low'].rolling(14).min()) * -100

        # --- Last values ---
        last_values = {
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
            'Bull/Bear': bull_bear.iloc[-1]
        }

        # --- Signals ---
        last_signals = {
            'Stock': ticker,
            'RSI Signal': "BUY" if last_values['RSI']<30 else "SELL" if last_values['RSI']>70 else "NEUTRAL",
            'Stoch Signal': "BUY" if last_values['Stoch']<20 else "SELL" if last_values['Stoch']>80 else "NEUTRAL",
            'Stoch RSI Signal': "BUY" if last_values['Stoch RSI']<0.2 else "SELL" if last_values['Stoch RSI']>0.8 else "NEUTRAL",
            'MACD Signal': "BUY" if last_values['MACD']>0 else "SELL" if last_values['MACD']<0 else "NEUTRAL",
            'ADX Signal': "BUY" if last_values['ADX']>25 else "NEUTRAL",
            'Williams %R Signal': "BUY" if last_values['Williams %R']<-80 else "SELL" if last_values['Williams %R']>-20 else "NEUTRAL",
            'CCI Signal': "BUY" if last_values['CCI']<-100 else "SELL" if last_values['CCI']>100 else "NEUTRAL",
            'Ultimate Osc Signal': "BUY" if last_values['Ultimate Osc']<30 else "SELL" if last_values['Ultimate Osc']>70 else "NEUTRAL",
            'ROC Signal': "BUY" if last_values['ROC']>0 else "SELL" if last_values['ROC']<0 else "NEUTRAL",
            'Bull/Bear Signal': "BUY" if last_values['Bull/Bear']>0 else "SELL" if last_values['Bull/Bear']<0 else "NEUTRAL"
        }

        # --- Combined Signal ---
        score_list = [1 if v=="BUY" else -1 if v=="SELL" else 0 for k,v in last_signals.items() if "Signal" in k]
        last_signals['Combined Signal'] = "BUY" if sum(score_list)>0 else "SELL" if sum(score_list)<0 else "NEUTRAL"

        values_list.append(last_values)
        signals_list.append(last_signals)

    # --- Display tables ---
    st.subheader("Indicator Values")
    st.dataframe(pd.DataFrame(values_list))

    st.subheader("Signals")
    st.dataframe(pd.DataFrame(signals_list).style.applymap(highlight_signal, subset=[c for c in signals_list[0].keys() if "Signal" in c]))
