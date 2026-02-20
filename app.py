from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
import bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# ---------------------------
# DATABASE CONNECTION (Postgres)
# ---------------------------

DATABASE_URL = os.environ.get("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cursor = conn.cursor()


# ---------------------------
# CREATE TABLES IF NOT EXIST
# ---------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(150)
);
""")


# ---------------------------
# LOGIN PAGE
# ---------------------------

@app.route('/')
@app.route('/login')
def login():
    return render_template('login.html')


# ---------------------------
# HANDLE LOGIN
# ---------------------------

@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']

    cursor.execute(
        "SELECT * FROM users WHERE username = %s",
        (username,)
    )

    user = cursor.fetchone()

    if user:
        stored_password = user[2].encode('utf-8')

        if bcrypt.checkpw(password.encode('utf-8'), stored_password):
            session['user'] = user[1]
            return redirect(url_for('dashboard'))

    return "Invalid credentials. Try again."


# ---------------------------
# REGISTER
# ---------------------------

@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def handle_register():
    username = request.form['username']
    password = request.form['password']

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed)
        )
    except:
        return "Username already exists."

    return redirect(url_for('login'))


# ---------------------------
# DASHBOARD
# ---------------------------

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect(url_for('login'))

    cursor.execute("SELECT COUNT(*) FROM clients")
    total_clients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    return render_template(
        "dashboard.html",
        total_clients=total_clients,
        total_users=total_users,
        username=session['user']
    )


# ---------------------------
# VIEW CLIENTS
# ---------------------------

@app.route('/clients')
def view_clients():

    if 'user' not in session:
        return redirect(url_for('login'))

    search = request.args.get('search')

    if search:
        cursor.execute(
            "SELECT * FROM clients WHERE first_name ILIKE %s OR last_name ILIKE %s",
            (f"%{search}%", f"%{search}%")
        )
    else:
        cursor.execute("SELECT * FROM clients")

    clients = cursor.fetchall()

    return render_template('clients.html', clients=clients)


# ---------------------------
# ADD CLIENT
# ---------------------------

@app.route('/add', methods=['POST'])
def add_client():

    if 'user' not in session:
        return redirect(url_for('login'))

    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']

    cursor.execute(
        "INSERT INTO clients (first_name, last_name, email) VALUES (%s, %s, %s)",
        (first_name, last_name, email)
    )

    return redirect(url_for('view_clients'))


# ---------------------------
# EDIT CLIENT
# ---------------------------

@app.route('/edit/<int:id>')
def edit_client(id):

    if 'user' not in session:
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM clients WHERE id = %s", (id,))
    client = cursor.fetchone()

    return render_template('edit_client.html', client=client)


@app.route('/update/<int:id>', methods=['POST'])
def update_client(id):

    if 'user' not in session:
        return redirect(url_for('login'))

    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']

    cursor.execute(
        "UPDATE clients SET first_name=%s, last_name=%s, email=%s WHERE id=%s",
        (first_name, last_name, email, id)
    )

    return redirect(url_for('view_clients'))


# ---------------------------
# DELETE CLIENT
# ---------------------------

@app.route('/delete/<int:id>')
def delete_client(id):

    if 'user' not in session:
        return redirect(url_for('login'))

    cursor.execute("DELETE FROM clients WHERE id = %s", (id,))

    return redirect(url_for('view_clients'))


# ---------------------------
# RUN APP
# ---------------------------

if __name__ == "__main__":
    app.run()