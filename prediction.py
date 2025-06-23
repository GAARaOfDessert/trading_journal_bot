import schedule
import time
from predict_live import make_live_prediction  # assuming this function exists

# Run the prediction every hour
schedule.every().hour.at(":00").do(make_live_prediction)

print("⏰ Live prediction scheduler started...")

while True:
    schedule.run_pending()
    time.sleep(1)
