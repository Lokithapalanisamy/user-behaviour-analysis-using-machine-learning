import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

# Load data
df = pd.read_excel('output.xlsx')

# Feature engineering
df['last_failed_login'] = pd.to_datetime(df['last_failed_login'])
df['time_since_last_fail'] = (pd.Timestamp.now() - df['last_failed_login']).dt.total_seconds()
df['has_failed_before'] = df['failed_attempts'] > 0

# Prepare features
features = df[['failed_attempts', 'time_since_last_fail', 'has_failed_before']].fillna(0)

# Scale features
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)

# Train anomaly detection model
model = IsolationForest(contamination=0.1)
model.fit(scaled_features)

# Predict anomalies
df['anomaly_score'] = model.decision_function(scaled_features)
df['is_anomaly'] = model.predict(scaled_features)

# Train-test split for classification
X = df[['failed_attempts']].fillna(0)
y = df['is_locked']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train Logistic Regression model
log_reg_model = LogisticRegression()
log_reg_model.fit(X_train, y_train)

# Evaluate model accuracy
accuracy = log_reg_model.score(X_test, y_test)
print(f"Model accuracy: {accuracy:.2f}")

# Plot 1: Anomaly Score Distribution
plt.figure(figsize=(10, 6))
plt.hist(df['anomaly_score'], bins=30, color='skyblue', edgecolor='black')
plt.title('Anomaly Score Distribution')
plt.xlabel('Anomaly Score')
plt.ylabel('Frequency')
plt.show()

# Plot 2: Failed Attempts vs Anomalies
plt.figure(figsize=(10, 6))
plt.scatter(df['failed_attempts'], df['anomaly_score'], c=df['is_anomaly'], cmap='coolwarm', alpha=0.7)
plt.title('Failed Attempts vs Anomaly Score')
plt.xlabel('Failed Attempts')
plt.ylabel('Anomaly Score')
plt.colorbar(label='Anomaly')
plt.show()

# Plot 3: Anomalies Over Time
time_series = df.set_index(pd.to_datetime(df['last_failed_login'])).sort_index()
time_series_resampled = time_series['is_anomaly'].resample('D').sum()  # Resample by day

plt.figure(figsize=(10, 6))
time_series_resampled.plot(kind='line', color='red', linestyle='-', marker='o', title='Anomalies Over Time')
plt.ylabel('Number of Anomalies')
plt.xlabel('Date')
plt.show()

# Plot 4: Failed Attempts and Lock Status Over Time
plt.figure(figsize=(10, 6))
time_series['failed_attempts'].plot(label='Failed Attempts', alpha=0.7)
time_series['is_locked'].plot(label='Account Locked', linestyle='--', color='r')
plt.title('Failed Attempts and Account Lock Status Over Time')
plt.xlabel('Date')
plt.ylabel('Failed Attempts / Lock Status')
plt.legend()
plt.show()
