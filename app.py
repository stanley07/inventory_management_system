# app.py

from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from dotenv import dotenv_values

# Load environment variables
config = dotenv_values(".env")

# Create Flask app
app = Flask(__name__, template_folder='templates')

# Set up TiDB connection
db_connection = mysql.connector.connect(
    host=config["TIDB_HOST"],
    port=int(config["TIDB_PORT"]),
    user=config["TIDB_USER"],
    password=config["TIDB_PASS"],
    database=config["TIDB_DB"],
)

# Function to create the 'products' table if it doesn't exist
def create_products_table():
    try:
        cursor = db_connection.cursor()
        create_table_query = """
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10, 2) NOT NULL,
                stock INT NOT NULL
            )
        """
        cursor.execute(create_table_query)
        db_connection.commit()
        cursor.close()
    except Exception as e:
        print(f"An unexpected error occurred while creating the 'products' table: {e}")

# Function to create the 'orders' table if it doesn't exist
def create_orders_table():
    try:
        cursor = db_connection.cursor()
        create_table_query = """
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                total_amount DECIMAL(10, 2) NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """
        cursor.execute(create_table_query)
        db_connection.commit()
        cursor.close()
    except Exception as e:
        print(f"An unexpected error occurred while creating the 'orders' table: {e}")

# Call the functions to create the tables
create_products_table()
create_orders_table()

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Route to add a new product
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock = int(request.form['stock'])

        try:
            cursor = db_connection.cursor()
            insert_query = "INSERT INTO products (name, description, price, stock) VALUES (%s, %s, %s, %s)"
            data = (name, description, price, stock)
            cursor.execute(insert_query, data)
            db_connection.commit()
            cursor.close()

            return redirect(url_for('view_products'))
        except Exception as e:
            return f"An unexpected error occurred while adding the product: {e}"

    return render_template('add_product.html')

# Route to view all products
@app.route('/view_products')
def view_products():
    try:
        cursor = db_connection.cursor()
        select_query = "SELECT * FROM products"
        cursor.execute(select_query)
        products = cursor.fetchall()
        cursor.close()

        return render_template('view_products.html', products=products)
    except Exception as e:
        return f"An unexpected error occurred while fetching products: {e}"

# Route to add a new order
@app.route('/add_order', methods=['GET', 'POST'])
def add_order():
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])

        try:
            cursor = db_connection.cursor()
            select_query = "SELECT price, stock FROM products WHERE id = %s"
            cursor.execute(select_query, (product_id,))
            product_data = cursor.fetchone()
            if not product_data:
                return "Product not found."

            price, stock = product_data
            total_amount = price * quantity

            if quantity > stock:
                return "Insufficient stock for this order."

            insert_query = "INSERT INTO orders (product_id, quantity, total_amount) VALUES (%s, %s, %s)"
            data = (product_id, quantity, total_amount)
            cursor.execute(insert_query, data)

            # Reduce stock
            update_query = "UPDATE products SET stock = stock - %s WHERE id = %s"
            cursor.execute(update_query, (quantity, product_id))

            db_connection.commit()
            cursor.close()

            return redirect(url_for('view_orders'))
        except Exception as e:
            return f"An unexpected error occurred while adding the order: {e}"

    try:
        cursor = db_connection.cursor()
        select_query = "SELECT id, name FROM products"
        cursor.execute(select_query)
        products = cursor.fetchall()
        cursor.close()

        return render_template('add_order.html', products=products)
    except Exception as e:
        return f"An unexpected error occurred while fetching products: {e}"

# Route to view all orders
@app.route('/view_orders')
def view_orders():
    try:
        cursor = db_connection.cursor()
        select_query = """
            SELECT orders.id, products.name, orders.quantity, orders.total_amount, orders.order_date
            FROM orders
            INNER JOIN products ON orders.product_id = products.id
            ORDER BY orders.order_date DESC
        """
        cursor.execute(select_query)
        orders = cursor.fetchall()
        cursor.close()

        return render_template('view_orders.html', orders=orders)
    except Exception as e:
        return f"An unexpected error occurred while fetching orders: {e}"

if __name__ == '__main__':
    app.run(debug=False)