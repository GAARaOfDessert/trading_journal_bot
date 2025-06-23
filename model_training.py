import MetaTrader5 as mt5
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib 

# Initialize MT5
mt5.initialize()

# Fetch historical XAUUSD data
symbol = "XAUUSDm"  
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 500)
df = pd.DataFrame(rates)

# Convert timestamp to readable time
df['time'] = pd.to_datetime(df['time'], unit='s')

# Add a target column: 1 = price goes up next hour, 0 = down
df['target'] = (df['close'].shift(-1) > df['close']).astype(int)

# Use price features
features = df[['open', 'high', 'low', 'close']]
target = df['target']

# Remove last row with NaN target
features = features[:-1]
target = target[:-1]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, shuffle=False)

# Train model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Predict and evaluate
preds = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, preds))

#save model
joblib.dump(model, "model.pkl") 
print("✅ Model saved as model.pkl")
