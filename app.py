from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# -----------------------------------
# Database Initialization
# -----------------------------------
def init_db():
    conn = sqlite3.connect('expense_tracker.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Create expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()


# Initialize database when the app starts
init_db()


# -----------------------------------
# Routes
# -----------------------------------

# Home Page
@app.route('/')
def home():
    return render_template('index.html')


# Sign Up Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    message = ""

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()

        try:
            cursor.execute(
                'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                (name, email, password)
            )
            conn.commit()
            message = "Account created successfully! You can now log in."
        except sqlite3.IntegrityError:
            message = "User already exists!"

        conn.close()

    return render_template('signup.html', message=message)


# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()

        cursor.execute(
            'SELECT name FROM users WHERE email = ? AND password = ?',
            (email, password)
        )
        user = cursor.fetchone()

        conn.close()

        if user:
            name = user[0]
            return redirect(url_for('dashboard', name=name))
        else:
            message = "Invalid email or password."

    return render_template('login.html', message=message)


# Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    name = request.args.get('name', 'User')

    conn = sqlite3.connect('expense_tracker.db')
    cursor = conn.cursor()

    # Add a new expense
    if request.method == 'POST':
        amount = request.form['amount']
        category = request.form['category']
        description = request.form['description']

        cursor.execute(
            '''
            INSERT INTO expenses (user_name, amount, category, description)
            VALUES (?, ?, ?, ?)
            ''',
            (name, amount, category, description)
        )
        conn.commit()

    # Fetch all expenses for the logged-in user
    cursor.execute(
        '''
        SELECT amount, category, description
        FROM expenses
        WHERE user_name = ?
        ''',
        (name,)
    )
    rows = cursor.fetchall()
    conn.close()

    # Prepare expense list and calculate total expenses
    expenses = []
    total = 0

    for row in rows:
        amount = float(row[0])
        total += amount

        expenses.append({
            'amount': amount,
            'category': row[1],
            'description': row[2]
        })

    return render_template(
        'dashboard.html',
        name=name,
        expenses=expenses,
        total=total
    )


# Logout Route
@app.route('/logout')
def logout():
    return redirect(url_for('home'))


# Run the Flask App
if __name__ == '__main__':
    app.run(debug=True)