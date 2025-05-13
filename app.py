from flask import Flask, request, render_template, redirect, session, jsonify
import sqlite3
from datetime import datetime, timedelta
import pytz
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from user_agents import parse
from collections import defaultdict
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
app.secret_key = 'supersecretkey'
ALERT_EMAIL = os.getenv('ALERT_EMAIL')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

MAX_ATTEMPTS = 3
LOCK_TIME_MINUTES = 30
ALLOWED_START_HOUR = 9
ALLOWED_END_HOUR = 20

def send_alert_email(subject, message):
    if not ALERT_EMAIL or not EMAIL_PASSWORD:
        print("[Email Alert Error] Email credentials are not set properly.")
        return

    try:
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = ALERT_EMAIL
        msg['To'] = ALERT_EMAIL

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(ALERT_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)

        print("[Email Alert] Sent successfully.")
    except Exception as e:
        print("[Email Alert Error]:", e)


def get_login_status_counts():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT status, COUNT(*) 
        FROM login_logs 
        GROUP BY status
    """)
    
    rows = cursor.fetchall()
    conn.close()

    labels = [row[0].capitalize() for row in rows]
    data = [row[1] for row in rows]
    
    return data, labels
# ----------------- Utility Functions -----------------

def get_user(username):
    con = sqlite3.connect('users.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    con.close()  # Ensure the connection is closed
    return user

def reset_login_attempts(username):
    con = sqlite3.connect('users.db')
    cur = con.cursor()
    cur.execute("UPDATE users SET failed_attempts = 0, is_locked = 0, last_failed_login = NULL WHERE username = ?", (username,))
    con.commit()
    con.close()

def increment_login_attempts(username):
    user = get_user(username)
    if not user:
        print(f"Error: User '{username}' not found.")
        return
    attempts = user['failed_attempts'] + 1
    is_locked = 1 if attempts >= MAX_ATTEMPTS else 0
    con = sqlite3.connect('users.db')
    cur = con.cursor()
    cur.execute("""
        UPDATE users SET failed_attempts = ?, last_failed_login = ?, is_locked = ?
        WHERE username = ?
    """, (attempts, datetime.now().isoformat(), is_locked, username))
    con.commit()
    con.close()

def is_within_login_time():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    return ALLOWED_START_HOUR <= now.hour < ALLOWED_END_HOUR

def is_login_from_india(ip):
    # Allow localhost for local testing
    if ip.startswith("127.") or ip == "localhost" or ip == "::1":
        return True
    try:
        response = requests.get(f"https://ipapi.co/{ip}/country/")
        country_code = response.text.strip()
        print(f"[GeoCheck] IP: {ip} | Country: {country_code}")
        return country_code == "IN"
    except Exception as e:
        print("[GeoCheck Error]:", e)
        return False



def log_login_attempt(username, ip, status, user_agent):
    timestamp = datetime.now().isoformat()
    browser = user_agent.browser.family
    platform = user_agent.os.family
    device = user_agent.device.family

    # Get location
    location = "Unknown"
    try:
        geo_response = requests.get(f"https://ipapi.co/{ip}/city/")
        location = geo_response.text.strip()
    except Exception as e:
        print("[GeoLocation Fetch Error]:", e)

    con = sqlite3.connect("users.db")
    cur = con.cursor()
    cur.execute("""
        INSERT INTO login_logs (username, ip_address, timestamp, browser, device, status, location)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (username, ip, timestamp, browser, device, status, location))
    con.commit()
    con.close()
    if "Anomaly" in status:
        send_alert_email(
            subject=f"[ALERT] {status} - {username}",
            message=f"User: {username}\nIP: {ip}\nStatus: {status}\nDevice: {device}, Browser: {browser}, Time: {timestamp}"
        )


# ----------------- Routes -----------------

@app.route('/')
def home():
    return render_template('register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if get_user(username):
            return render_template('register.html', error="Username already exists.")
        password_hash = generate_password_hash(password)
        con = sqlite3.connect('users.db')
        cur = con.cursor()
        cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        con.commit()
        con.close()
        return render_template('login.html', success="Registration successful. Please log in.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        ua_string = request.headers.get('User-Agent')
        user_agent = parse(ua_string)

        # Geo Check
        if not is_login_from_india(ip):
            log_login_attempt(username, ip, 'Anomaly - Outside India', user_agent)
            return render_template('login.html', error="Login allowed only from India")

        # Time Check
        if not is_within_login_time():
            log_login_attempt(username, ip, 'Anomaly - Time Restriction', user_agent)
            return render_template('login.html', error="Login allowed only between 9AM - 5PM IST")

        user = get_user(username)
        if user:
            # If account is locked
            if user['is_locked']:
                last_failed_time = datetime.fromisoformat(user['last_failed_login'])
                if datetime.now() - last_failed_time < timedelta(minutes=LOCK_TIME_MINUTES):
                    remaining = (last_failed_time + timedelta(minutes=LOCK_TIME_MINUTES)) - datetime.now()
                    mins_left = remaining.seconds // 60
                    log_login_attempt(username, ip, f'Anomaly - Account Locked ({mins_left} min left)', user_agent)
                    return render_template('login.html', error=f"Account locked. Try again in {mins_left} minutes.")
                else:
                    reset_login_attempts(username)  # Unlock after timeout

            # Check password
            if check_password_hash(user['password_hash'], password):
                reset_login_attempts(username)
                log_login_attempt(username, ip, 'Normal', user_agent)
                session['user'] = username
                return render_template('afterlogin.html')
            else:
                increment_login_attempts(username)
                remaining_attempts = MAX_ATTEMPTS - (user['failed_attempts'] + 1)
                if remaining_attempts <= 0:
                    log_login_attempt(username, ip, 'Anomaly - Account Locked', user_agent)
                    return render_template('login.html', error="Too many failed attempts. Account locked for 30 minutes.")
                else:
                    log_login_attempt(username, ip, 'Anomaly - Wrong Password', user_agent)
                    return render_template('login.html', error=f"Invalid credentials. {remaining_attempts} attempts left.")
        else:
            log_login_attempt(username, ip, 'Anomaly - No User', user_agent)
            return render_template('login.html', error="User not found.")
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    con = sqlite3.connect('users.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    # Fetch all logs ordered by time
    cur.execute("SELECT * FROM login_logs ORDER BY timestamp DESC")
    logs = cur.fetchall()

    # Anomaly detection
    user_logs = defaultdict(list)
    anomalies = []
    normal = []

    for log in logs:
        key = (log['username'], log['browser'], log['device'], log['ip_address'])

        if key in user_logs[log['username']]:
            status = 'Normal'
        else:
            # First time seeing this combination for this user
            status = 'Anomaly'
            anomalies.append(log)
        
        user_logs[log['username']].append(key)

    # Re-process logs with labels
    processed_logs = []
    for log in logs:
        key = (log['username'], log['browser'], log['device'], log['ip_address'])
        status = 'Normal' if user_logs[log['username']].count(key) > 1 else 'Anomaly'

        processed_logs.append({
            'timestamp': log['timestamp'],
            'username': log['username'],
            'ip': log['ip_address'],
            'location': log.get('location', 'Unknown'),
            'browser': log['browser'],
            'device': log['device'],
            'status': status
        })



    # Stats for pie chart
    total_events = len(processed_logs)
    anomaly_count = sum(1 for log in processed_logs if log['status'] == 'Anomaly')
    normal_count = total_events - anomaly_count

    return render_template('dashboard.html',
                           logs=processed_logs,
                           total=total_events,
                           anomaly=anomaly_count,
                           normal=normal_count)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    con = sqlite3.connect('users.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    if request.method == 'POST':
        username = request.form['username']
        reset_login_attempts(username)

    cur.execute("SELECT username, is_locked, failed_attempts FROM users")
    users = cur.fetchall()
    con.close()
    return render_template('admin.html', users=users)


if __name__ == '__main__':
    app.run(debug=True)

