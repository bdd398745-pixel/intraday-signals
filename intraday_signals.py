if stocks_input:
    tickers = [s.strip() for s in stocks_input.split(",")]
    values_list = []
    signals_list = []

    for ticker in tickers:
        df = fetch_data(ticker, interval, period)
        if df.empty:
            st.warning(f"No data for {ticker}")
            continue

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

        df['EMA13'] = df['Close'].ewm(span=13, adjust=False).mean()
        bull_bear = df['High'] - df['EMA13']

        will_r = (df['Close'] - df['High'].rolling(14).max()) / (
            df['High'].rolling(14).max() - df['Low'].rolling(14).min()
        ) * -100

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

        last_signals = {
            'Stock': ticker,
            'RSI Signal': signal_rsi(last_values['RSI']),
            'Stoch Signal': signal_stoch(last_values['Stoch']),
            'Stoch RSI Signal': signal_stochrsi(last_values['Stoch RSI']),
            'MACD Signal': signal_macd(last_values['MACD']),
            'ADX Signal': signal_adx(last_values['ADX']),
            'Williams %R Signal': signal_willr(last_values['Williams %R']),
            'CCI Signal': signal_cci(last_values['CCI']),
            'Ultimate Osc Signal': signal_ultosc(last_values['Ultimate Osc']),
            'ROC Signal': signal_roc(last_values['ROC']),
            'Bull/Bear Signal': signal_bb(last_values['Bull/Bear'])
        }

        # --- Combined Signal ---
        scores = [1 if v=="BUY" else -1 if v=="SELL" else 0 for v in last_signals.values() if 'Signal' in _]
        last_signals['Combined Signal'] = "BUY" if sum(scores) > 0 else "SELL" if sum(scores) < 0 else "NEUTRAL"

        values_list.append(last_values)
        signals_list.append(last_signals)

    # --- Display Indicator Values ---
    st.subheader("Indicator Values")
    df_values = pd.DataFrame(values_list)
    st.dataframe(df_values)

    # --- Display Signals ---
    st.subheader("Signals")
    df_signals = pd.DataFrame(signals_list)
    st.dataframe(df_signals.style.applymap(
        highlight_signal, 
        subset=[c for c in df_signals.columns if 'Signal' in c]
    ))
