import MetaTrader5 as mt5
import pandas as pd
import joblib
import json
import asyncio
from telegram import Bot

async def make_live_prediction(bot):
    if not mt5.initialize():
        print("❌ Failed to initialize MT5")
        return

    symbol = "XAUUSDm"
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 500)
    if rates is None or len(rates) < 2:
        print("❌ Not enough data to make prediction")
        return

    df = pd.DataFrame(rates)
    df['target'] = df['close'].shift(-1) > df['close']
    df['target'] = df['target'].astype(int)

    latest = df.iloc[-2][['open', 'high', 'low', 'close']].values.reshape(1, -1)
    model = joblib.load("model.pkl")

    prediction = model.predict(latest)
    direction = "📈 XAUUSD will go UP" if prediction[0] == 1 else "📉 XAUUSD will go DOWN"
    print(f"[LIVE PREDICTION] {direction}")

    with open("user_data.json") as f:
        data = json.load(f)

    for user in data.values():
        user_id = user.get("user_id")
        if user_id:
            try:
                await bot.send_message(chat_id=user_id, text=f"🧠 ML Prediction:\n{direction}")
            except Exception as e:
                print(f"❌ Error sending to {user_id}: {e}")