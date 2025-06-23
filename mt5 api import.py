import MetaTrader5 as mt5
import pandas as pd

mt5.initialize()

# Fetch 500 hourly candles for XAUUSD
rates = mt5.copy_rates_from_pos("XAUUSDm", mt5.TIMEFRAME_M30, 0, 500)


# Shut down connection
mt5.shutdown()

# Load into DataFrame and format
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

# Show the last 5 rows
print(df[['time', 'open', 'high', 'low', 'close']].tail())

df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
print(df[['time', 'close', 'target']].tail(10))