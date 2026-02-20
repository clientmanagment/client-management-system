import os
import psycopg2
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")


# ==============================
# DATABASE CONNECTION
# ==============================
def get_db_connection():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    return conn


# ==============================
# CREATE TABLES IF NOT EXIST
# ==============================
def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100),
            phone VARCHAR(50)
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


create_tables()


# ==============================
# HOME
# ==============================
@app.route('/')
def home():
    return redirect(url_for('login'))


# ==============================
# REGISTER
# ==============================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed.decode('utf-8'))
            )
            conn.commit()
            flash("Registration successful. Please login.")
            return redirect(url_for('login'))
        except:
            flash("Username already exists.")
        finally:
            cur.close()
            conn.close()

    return render_template('register.html')


# ==============================
# LOGIN
# ==============================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[0].encode('utf-8')):
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials")

    return render_template('login.html')


# ==============================
# DASHBOARD
# ==============================
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM clients")
    total_clients = cur.fetchone()[0]
    cur.close()
    conn.close()

    return render_template('dashboard.html',
                           username=session['user'],
                           total_clients=total_clients)


# ==============================
# LOGOUT
# ==============================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)