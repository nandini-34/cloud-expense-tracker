from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "cloud_expense_tracker_secret_key_123"


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
    # If user is already logged in, go directly to dashboard
    if 'user_name' in session:
        return redirect(url_for('dashboard'))

    return render_template('index.html')


# Sign Up Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # If user is already logged in, go directly to dashboard
    if 'user_name' in session:
        return redirect(url_for('dashboard'))

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
    # If user is already logged in, go directly to dashboard
    if 'user_name' in session:
        return redirect(url_for('dashboard'))

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
            # Save login information in session
            session['user_name'] = user[0]
            session['user_email'] = email

            # Redirect to dashboard
            return redirect(url_for('dashboard'))
        else:
            message = "Invalid email or password."

    return render_template('login.html', message=message)


# Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # Check if user is logged in
    if 'user_name' not in session:
        return redirect(url_for('login'))

    # Get logged-in user's name from session
    name = session['user_name']

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

    # -----------------------------------
    # Analytics Calculations
    # -----------------------------------
    transaction_count = len(expenses)

    categories = set()
    category_totals = {}

    for expense in expenses:
        category = expense['category']
        categories.add(category)

        if category in category_totals:
            category_totals[category] += expense['amount']
        else:
            category_totals[category] = expense['amount']

    category_count = len(categories)

    # Prepare data for Chart.js
    chart_labels = list(category_totals.keys())
    chart_values = list(category_totals.values())

    # Render dashboard with analytics and chart data
    return render_template(
        'dashboard.html',
        name=name,
        expenses=expenses,
        total=total,
        transaction_count=transaction_count,
        category_count=category_count,
        chart_labels=chart_labels,
        chart_values=chart_values
    )


# Logout Route
@app.route('/logout')
def logout():
    # Remove all session data
    session.clear()

    # Redirect to home page
    return redirect(url_for('home'))


# Run the Flask App
if __name__ == '__main__':
    app.run(debug=True)