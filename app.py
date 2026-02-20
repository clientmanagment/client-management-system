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
    return psycopg2.connect(os.environ["DATABASE_URL"])


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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)

            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed.decode('utf-8'))
            )

            conn.commit()
            flash("Registration successful.")
            return redirect(url_for('login'))

        except Exception as e:
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

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

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

    return render_template('dashboard.html', username=session['user'])


# ==============================
# LOGOUT
# ==============================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run()