import sqlite3
import matplotlib.pyplot as plt

# Path to your SQLite database
DB_PATH = 'users.db'

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Fetch status counts from the login_logs table
cursor.execute("SELECT status, COUNT(*) FROM login_logs GROUP BY status")
rows = cursor.fetchall()

conn.close()

# Prepare data for pie chart
labels = [row[0] for row in rows]
data = [row[1] for row in rows]

# Plot the donut chart
fig, ax = plt.subplots(figsize=(6, 6))
wedges, texts, autotexts = ax.pie(
    data,
    labels=labels,
    autopct='%1.1f%%',
    startangle=90,
    pctdistance=0.85,
    wedgeprops=dict(width=0.4, edgecolor='w')  # donut style
)

# Draw center white circle to create donut effect
centre_circle = plt.Circle((0, 0), 0.55, fc='white')
fig.gca().add_artist(centre_circle)

# Title and layout
plt.title("Login Status Distribution")
ax.axis('equal')  # Equal aspect ratio ensures the pie is a circle
plt.tight_layout()

# Save or show the chart
plt.savefig("login_status_donut_chart.png")
plt.show()
