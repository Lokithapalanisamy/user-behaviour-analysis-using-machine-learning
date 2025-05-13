import sqlite3


# Connect to the SQLite database
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Add the 'location' column
cursor.execute('''
    ALTER TABLE login_logs
    ADD COLUMN location TEXT;
''')

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Column 'location' added successfully to 'login_logs' table.")
