import sqlite3

def get_db():
    return sqlite3.connect("contacts.db")

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT,
        company TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_contact(name, phone, email, company):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO contacts (name, phone, email, company) VALUES (?, ?, ?, ?)",
        (name, phone, email, company)
    )
    conn.commit()
    conn.close()

def get_contacts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, phone, email, company FROM contacts")
    data = cur.fetchall()
    conn.close()
    return data
