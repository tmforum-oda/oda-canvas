"""
Lightweight demo version of the microservice using only built-in Python modules.
This demonstrates the core functionality without external dependencies.
"""

import json
import sqlite3
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class MicroserviceDB:
    """Simple database layer using SQLite"""
    
    def __init__(self, db_path="demo_microservice.db"):
        self.db_path = db_path
        self.init_db()
        self.seed_data()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock_quantity INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Database initialized successfully!")
    
    def seed_data(self):
        """Add sample data if tables are empty"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            # Add sample users
            users = [
                ("john_doe", "john.doe@example.com", "John Doe"),
                ("jane_smith", "jane.smith@example.com", "Jane Smith"),
                ("bob_wilson", "bob.wilson@example.com", "Bob Wilson")
            ]
            cursor.executemany("INSERT INTO users (username, email, full_name) VALUES (?, ?, ?)", users)
            
            # Add sample products
            products = [
                ("Laptop", "High-performance laptop", 1299.99, 50),
                ("Smartphone", "Latest smartphone", 799.99, 100),
                ("Headphones", "Wireless headphones", 299.99, 75),
                ("Tablet", "Lightweight tablet", 499.99, 30),
                ("Smart Watch", "Fitness tracking watch", 249.99, 60)
            ]
            cursor.executemany("INSERT INTO products (name, description, price, stock_quantity) VALUES (?, ?, ?, ?)", products)
            
            # Add sample orders
            cursor.execute("INSERT INTO orders (user_id, total_amount, status) VALUES (1, 1599.98, 'confirmed')")
            order_id = cursor.lastrowid
            cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, 1, 1, 1299.99)", (order_id,))
            cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, 3, 1, 299.99)", (order_id,))
            
            conn.commit()
            print("✓ Sample data added successfully!")
        
        conn.close()
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """Execute database query"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        result = None
        if fetch_one:
            result = dict(cursor.fetchone()) if cursor.fetchone() else None
            cursor.execute(query, params) if params else cursor.execute(query)  # Re-execute for fetchone
            row = cursor.fetchone()
            result = dict(row) if row else None
        elif fetch_all:
            result = [dict(row) for row in cursor.fetchall()]
        else:
            conn.commit()
            result = cursor.lastrowid
        
        conn.close()
        return result

class MicroserviceHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the microservice"""
    
    def __init__(self, *args, **kwargs):
        self.db = MicroserviceDB()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/":
            self.send_welcome()
        elif path == "/health":
            self.send_json_response({"status": "healthy", "message": "Microservice is running"})
        elif path == "/stats":
            self.send_stats()
        elif path == "/users":
            self.get_users()
        elif path.startswith("/users/"):
            user_id = path.split("/")[-1]
            self.get_user(user_id)
        elif path == "/products":
            self.get_products()
        elif path.startswith("/products/"):
            product_id = path.split("/")[-1]
            self.get_product(product_id)
        elif path == "/orders":
            self.get_orders()
        elif path.startswith("/orders/"):
            order_id = path.split("/")[-1]
            self.get_order(order_id)
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8')) if post_data else {}
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return
        
        if path == "/users":
            self.create_user(data)
        elif path == "/products":
            self.create_product(data)
        elif path == "/orders":
            self.create_order(data)
        else:
            self.send_error(404, "Endpoint not found")
    
    def send_welcome(self):
        """Send welcome page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>FastAPI E-Commerce Microservice Demo</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
                .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #2c5aa0; }
                .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #2c5aa0; }
                .method { font-weight: bold; color: #2c5aa0; }
                .description { color: #666; margin-top: 5px; }
                a { color: #2c5aa0; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 FastAPI E-Commerce Microservice Demo</h1>
                <p>Willkommen zum demonstrativen Python-Microservice mit CRUD-Funktionen und relationalen Datenmodellen!</p>
                
                <h2>📡 Verfügbare API-Endpunkte:</h2>
                
                <div class="endpoint">
                    <span class="method">GET</span> <a href="/health">/health</a>
                    <div class="description">Health-Check des Services</div>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <a href="/stats">/stats</a>
                    <div class="description">Systemstatistiken</div>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <a href="/users">/users</a>
                    <div class="description">Alle Benutzer auflisten</div>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <a href="/users/1">/users/{id}</a>
                    <div class="description">Benutzer nach ID abrufen</div>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <a href="/products">/products</a>
                    <div class="description">Alle Produkte auflisten</div>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <a href="/products/1">/products/{id}</a>
                    <div class="description">Produkt nach ID abrufen</div>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <a href="/orders">/orders</a>
                    <div class="description">Alle Bestellungen auflisten</div>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <a href="/orders/1">/orders/{id}</a>
                    <div class="description">Bestellung nach ID abrufen</div>
                </div>
                
                <h3>🔧 POST Endpunkte (für Tests mit Tools wie Postman oder curl):</h3>
                <p><strong>POST /users</strong> - Neuen Benutzer erstellen</p>
                <p><strong>POST /products</strong> - Neues Produkt erstellen</p>
                <p><strong>POST /orders</strong> - Neue Bestellung erstellen</p>
                
                <h3>🎯 Features:</h3>
                <ul>
                    <li>✓ Eingebettete SQLite-Datenbank</li>
                    <li>✓ Relationale Datenmodelle (Users, Products, Orders, OrderItems)</li>
                    <li>✓ CRUD-Operationen</li>
                    <li>✓ JSON API-Responses</li>
                    <li>✓ Testdaten bereits geladen</li>
                </ul>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        response = json.dumps(data, indent=2, ensure_ascii=False)
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def send_stats(self):
        """Get system statistics"""
        user_count = self.db.execute_query("SELECT COUNT(*) as count FROM users", fetch_one=True)
        product_count = self.db.execute_query("SELECT COUNT(*) as count FROM products", fetch_one=True)
        order_count = self.db.execute_query("SELECT COUNT(*) as count FROM orders", fetch_one=True)
        
        stats = {
            "total_users": user_count["count"] if user_count else 0,
            "total_products": product_count["count"] if product_count else 0,
            "total_orders": order_count["count"] if order_count else 0,
            "timestamp": datetime.now().isoformat()
        }
        self.send_json_response(stats)
    
    def get_users(self):
        """Get all users"""
        users = self.db.execute_query("SELECT * FROM users ORDER BY id", fetch_all=True)
        self.send_json_response({"users": users, "count": len(users)})
    
    def get_user(self, user_id):
        """Get user by ID"""
        user = self.db.execute_query("SELECT * FROM users WHERE id = ?", (user_id,), fetch_one=True)
        if user:
            # Get user's orders
            orders = self.db.execute_query("SELECT * FROM orders WHERE user_id = ?", (user_id,), fetch_all=True)
            user["orders"] = orders
            self.send_json_response(user)
        else:
            self.send_json_response({"error": "User not found"}, 404)
    
    def get_products(self):
        """Get all products"""
        products = self.db.execute_query("SELECT * FROM products ORDER BY id", fetch_all=True)
        self.send_json_response({"products": products, "count": len(products)})
    
    def get_product(self, product_id):
        """Get product by ID"""
        product = self.db.execute_query("SELECT * FROM products WHERE id = ?", (product_id,), fetch_one=True)
        if product:
            self.send_json_response(product)
        else:
            self.send_json_response({"error": "Product not found"}, 404)
    
    def get_orders(self):
        """Get all orders with details"""
        orders = self.db.execute_query("""
            SELECT o.*, u.username, u.full_name as user_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.id
        """, fetch_all=True)
        
        # Get order items for each order
        for order in orders:
            items = self.db.execute_query("""
                SELECT oi.*, p.name as product_name, p.description
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            """, (order["id"],), fetch_all=True)
            order["order_items"] = items
        
        self.send_json_response({"orders": orders, "count": len(orders)})
    
    def get_order(self, order_id):
        """Get order by ID with full details"""
        order = self.db.execute_query("""
            SELECT o.*, u.username, u.full_name as user_name, u.email
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = ?
        """, (order_id,), fetch_one=True)
        
        if order:
            # Get order items
            items = self.db.execute_query("""
                SELECT oi.*, p.name as product_name, p.description, p.price
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            """, (order_id,), fetch_all=True)
            order["order_items"] = items
            self.send_json_response(order)
        else:
            self.send_json_response({"error": "Order not found"}, 404)
    
    def create_user(self, data):
        """Create new user"""
        try:
            user_id = self.db.execute_query(
                "INSERT INTO users (username, email, full_name) VALUES (?, ?, ?)",
                (data["username"], data["email"], data["full_name"])
            )
            new_user = self.db.execute_query("SELECT * FROM users WHERE id = ?", (user_id,), fetch_one=True)
            self.send_json_response(new_user, 201)
        except Exception as e:
            self.send_json_response({"error": f"Failed to create user: {str(e)}"}, 400)
    
    def create_product(self, data):
        """Create new product"""
        try:
            product_id = self.db.execute_query(
                "INSERT INTO products (name, description, price, stock_quantity) VALUES (?, ?, ?, ?)",
                (data["name"], data.get("description"), data["price"], data.get("stock_quantity", 0))
            )
            new_product = self.db.execute_query("SELECT * FROM products WHERE id = ?", (product_id,), fetch_one=True)
            self.send_json_response(new_product, 201)
        except Exception as e:
            self.send_json_response({"error": f"Failed to create product: {str(e)}"}, 400)
    
    def create_order(self, data):
        """Create new order"""
        try:
            # Calculate total
            total_amount = sum(item["quantity"] * item["unit_price"] for item in data["order_items"])
            
            # Create order
            order_id = self.db.execute_query(
                "INSERT INTO orders (user_id, total_amount, status) VALUES (?, ?, ?)",
                (data["user_id"], total_amount, data.get("status", "pending"))
            )
            
            # Create order items
            for item in data["order_items"]:
                self.db.execute_query(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (order_id, item["product_id"], item["quantity"], item["unit_price"])
                )
            
            # Return created order
            self.get_order(order_id)
        except Exception as e:
            self.send_json_response({"error": f"Failed to create order: {str(e)}"}, 400)

def start_server(port=8000):
    """Start the microservice server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MicroserviceHandler)
    print(f"🚀 Microservice gestartet auf http://localhost:{port}")
    print(f"📖 Öffnen Sie http://localhost:{port} im Browser für die API-Dokumentation")
    print("🛑 Drücken Sie Ctrl+C zum Beenden")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server wird beendet...")
        httpd.shutdown()

if __name__ == "__main__":
    start_server(8080)  # Use port 8080 instead of 8000