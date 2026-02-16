from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import csv
from io import StringIO, BytesIO

app = Flask(__name__)
app.secret_key = "supersecretkey"


# -----------------------------
# DATABASE
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
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


# -----------------------------
# HARDCODED USERS
# -----------------------------
ADMIN_USER = {"username": "admin", "password": "admin123"}
CUSTOMER_USER = {"username": "customer", "password": "cust123"}


# -----------------------------
# ROUTES
# -----------------------------

@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/role")
def role():
    return render_template("role.html")


# -----------------------------
# ADMIN LOGIN
# -----------------------------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USER["username"] and password == ADMIN_USER["password"]:
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid Admin Credentials!"

    return render_template("admin_login.html", error=error)


# -----------------------------
# CUSTOMER LOGIN
# -----------------------------
@app.route("/customer_login", methods=["GET", "POST"])
def customer_login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == CUSTOMER_USER["username"] and password == CUSTOMER_USER["password"]:
            session["role"] = "customer"
            return redirect(url_for("customer_page"))
        else:
            error = "Invalid Customer Credentials!"

    return render_template("customer_login.html", error=error)


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("welcome"))


# -----------------------------
# CUSTOMER PAGE
# -----------------------------
@app.route("/customer", methods=["GET", "POST"])
def customer_page():
    if session.get("role") != "customer":
        return redirect(url_for("customer_login"))

    msg = None

    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        company = request.form.get("company")

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO contacts (name, phone, email, company) VALUES (?, ?, ?, ?)",
            (name, phone, email, company)
        )
        conn.commit()
        conn.close()

        msg = "Contact saved successfully ✅"

    return render_template("customer.html", msg=msg)


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    contacts = conn.execute("SELECT * FROM contacts ORDER BY id DESC").fetchall()
    conn.close()

    return render_template("admin_dashboard.html", contacts=contacts)


# -----------------------------
# VIEW DETAILS PAGE
# -----------------------------
@app.route("/view_details/<int:contact_id>")
def view_details(contact_id):
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    contact = conn.execute(
        "SELECT * FROM contacts WHERE id = ?",
        (contact_id,)
    ).fetchone()
    conn.close()

    if contact is None:
        return "Contact not found", 404

    return render_template("admin_details.html", contact=contact)


# -----------------------------
# COMPANY WISE CONTACTS
# -----------------------------
@app.route("/company_contacts")
def company_contacts():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    data = conn.execute("""
        SELECT company, COUNT(*) as total
        FROM contacts
        GROUP BY company
        ORDER BY total DESC
    """).fetchall()
    conn.close()

    return render_template("company_contacts.html", data=data)


# -----------------------------
# EMAIL DOMAIN DISTRIBUTION
# -----------------------------
@app.route("/email_distribution")
def email_distribution():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    contacts = conn.execute("SELECT email FROM contacts").fetchall()
    conn.close()

    domain_count = {}

    for c in contacts:
        email = c["email"]
        if email and "@" in email:
            domain = email.split("@")[1].lower()
            domain_count[domain] = domain_count.get(domain, 0) + 1

    return render_template("email_distribution.html", domain_count=domain_count)


# -----------------------------
# EXPORT CSV
# -----------------------------
@app.route("/export_csv")
def export_csv():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    contacts = conn.execute("SELECT * FROM contacts").fetchall()
    conn.close()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "Name", "Phone", "Email", "Company"])

    for c in contacts:
        writer.writerow([c["id"], c["name"], c["phone"], c["email"], c["company"]])

    output = BytesIO()
    output.write(si.getvalue().encode("utf-8"))
    output.seek(0)

    return send_file(output, mimetype="text/csv", as_attachment=True, download_name="contacts.csv")


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)