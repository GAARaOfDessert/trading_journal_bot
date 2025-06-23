import asyncio
from datetime import datetime
from predict_live import make_live_prediction
from telegram import Bot

# Initialize your bot
BOT_TOKEN = "7613652813:AAFnKLGASHpx7thBOs48eIt4eSyGFbiFO7c"
bot = Bot(token=BOT_TOKEN)

async def scheduler():
    print("⏰ Live prediction scheduler started...")
    last_prediction_minute = None

    while True:
        now = datetime.now()

        # Only run at :00 or :30 and not more than once per minute
        if now.minute in [0, 30] and now.second == 0 and now.minute != last_prediction_minute:
            await make_live_prediction(bot)
            last_prediction_minute = now.minute

        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(scheduler())
