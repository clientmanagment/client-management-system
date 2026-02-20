from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="vacation4@",   # keep your real password here
    database="student_db"
)

cursor = db.cursor()

# =============================
# LOGIN PAGE
# =============================

@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def handle_register():
    username = request.form['username']
    password = request.form['password']

    # Hash password
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    cursor.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, hashed)
    )
    db.commit()

    return redirect(url_for('login'))


@app.route('/')
@app.route('/login')
def login():
    return render_template('login.html')


# =============================
# HANDLE LOGIN (bcrypt)
# =============================

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


# =============================
# LOGOUT
# =============================

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# =============================
# VIEW CLIENTS (Protected)
# =============================

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect(url_for('login'))

    # Count total clients
    cursor.execute("SELECT COUNT(*) FROM clients")
    total_clients = cursor.fetchone()[0]

    # Count total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    return render_template(
        "dashboard.html",
        total_clients=total_clients,
        total_users=total_users,
        username=session['user']
    )


@app.route('/clients')
def view_clients():

    if 'user' not in session:
        return redirect(url_for('login'))

    search = request.args.get('search')

    if search:
        cursor.execute(
            "SELECT * FROM clients WHERE first_name LIKE %s OR last_name LIKE %s",
            (f"%{search}%", f"%{search}%")
        )
    else:
        cursor.execute("SELECT * FROM clients")

    clients = cursor.fetchall()
    total = len(clients)

    return render_template('clients.html', clients=clients, total=total)


# =============================
# ADD CLIENT
# =============================

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

    db.commit()

    return redirect(url_for('view_clients'))


# =============================
# EDIT CLIENT
# =============================

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

    db.commit()

    return redirect(url_for('view_clients'))


# =============================
# DELETE CLIENT
# =============================

@app.route('/delete/<int:id>')
def delete_client(id):

    if 'user' not in session:
        return redirect(url_for('login'))

    cursor.execute("DELETE FROM clients WHERE id = %s", (id,))
    db.commit()

    return redirect(url_for('view_clients'))


# =============================
# RUN APP
# =============================

if __name__ == '__main__':
    app.run(debug=True)
