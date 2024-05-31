from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
def get_db_connection():
    conn = sqlite3.connect('pos_system.db')
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/add_product', methods=('GET', 'POST'))
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        quantity = request.form['quantity']
        
        if not name or not price or not quantity:
            flash('All fields are required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)', 
                         (name, price, quantity))
            conn.commit()
            conn.close()
            flash('Product added successfully!')
            return redirect(url_for('index'))
    
    return render_template('add_product.html')

@app.route('/process_sale', methods=('GET', 'POST'))
def process_sale():
    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = request.form['quantity']
        
        conn = get_db_connection()
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        
        if product is None:
            flash('Product not found!')
        elif product['quantity'] < int(quantity):
            flash('Insufficient stock!')
        else:
            total_price = product['price'] * int(quantity)
            conn.execute('INSERT INTO sales (product_id, quantity, total_price) VALUES (?, ?, ?)', 
                         (product_id, quantity, total_price))
            conn.execute('UPDATE products SET quantity = quantity - ? WHERE id = ?', 
                         (quantity, product_id))
            conn.commit()
            flash('Sale processed successfully!')
        
        conn.close()
    
    return render_template('process_sale.html')

@app.route('/report')
def report():
    conn = get_db_connection()
    sales = conn.execute('''
        SELECT p.name, s.quantity, s.total_price, s.sale_date
        FROM sales s JOIN products p ON s.product_id = p.id
    ''').fetchall()
    conn.close()
    return render_template('report.html', sales=sales)

@app.route('/stock')
def stock():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products WHERE quantity > 0').fetchall()
    conn.close()
    return render_template('stock.html', products=products)

    
@app.route('/delete_product/<int:id>', methods=['POST'])
def delete_product(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Product deleted successfully!')
    return redirect(url_for('index'))


# Initialize database
def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        price REAL NOT NULL,
                        quantity INTEGER NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER,
                        quantity INTEGER,
                        total_price REAL,
                        sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products (id))''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
