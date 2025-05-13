import sqlite3

# Connect to SQLite DB (it will create users.db if not exists)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    failed_attempts INTEGER DEFAULT 0,
    last_failed_login TEXT,
    is_locked INTEGER DEFAULT 0
)
''')

# Create login_logs table
cursor.execute('''
CREATE TABLE IF NOT EXISTS login_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    ip_address TEXT,
    timestamp TEXT,
    browser TEXT,
    device TEXT,
    location TEXT,
    status TEXT
)
''')

# Commit and close
conn.commit()
conn.close()

print("✅ Database setup completed successfully.")