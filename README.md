🔐 User Login Behavior Anomaly Detection System
This Flask web application provides a secure user authentication system with intelligent anomaly detection based on location, time, device, and failed login attempts. Alerts are sent via email for any suspicious or unauthorized activity.

🧠 Features
✅ User Registration & Login System

🔐 Account Lockout after Failed Login Attempts

🌐 Geo-IP Restriction (Only logins from India allowed)

🕒 Time-Based Login Restriction (Only between 9 AM – 8 PM IST)

🧠 Anomaly Detection using Device/Browser/IP fingerprinting

✉️ Email Alerts for Unauthorized or Suspicious Logins

📊 Admin Dashboard with Login Logs and Statistics

📍 Location tagging using IP-based geolocation

🔧 Admin Panel to Unlock Users

🧰 Tech Stack
Backend: Python, Flask
Frontend: HTML (Jinja Templates)
Database: SQLite
Email: Gmail SMTP (smtplib)
IP Geolocation: ipapi.co
User Agent Parsing: user-agents library

📂 Folder Structure
├── app.py
├── templates/
│   ├── register.html
│   ├── login.html
│   ├── afterlogin.html
│   ├── dashboard.html
│   └── admin.html
├── static/
│   └── (optional CSS or JS files)
├── users.db
├── .env
└── README.md
⚙️ Setup Instructions
1. Clone the Repository
git clone https://github.com/yourusername/login-anomaly-detection.git
cd login-anomaly-detection
2. Create and Activate Virtual Environment (Recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
3. Install Dependencies
pip install -r requirements.txt
4. Create .env File
Create a .env file in the root directory:
ALERT_EMAIL_
