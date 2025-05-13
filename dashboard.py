from flask import Flask, render_template
import sqlite3
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

DB_PATH = 'users.db'
CHART_PATH = 'static/piechart.png'

# Get count of each status from login_logs
def get_login_status_counts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT status, COUNT(*) FROM login_logs GROUP BY status")
    rows = cursor.fetchall()
    conn.close()

    labels = [row[0] for row in rows]
    data = [row[1] for row in rows]

    return data, labels

# Generate pie chart and save it
def generate_pie_chart(data, labels, filename=CHART_PATH):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(data, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Make it a circle
    plt.title("Login Status Distribution")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

@app.route('/dashboard')
def dashboard():
    data, labels = get_login_status_counts()
    generate_pie_chart(data, labels)
    return render_template('dashboard.html', chart_url='/' + CHART_PATH)

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(debug=True)
