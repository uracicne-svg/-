"""
Shop IS - Flask + SQLite
Zavisimosti: tolko Flask (bcrypt zamenen na vstroennyy hashlib)
"""
import os
import sqlite3
import hashlib
import secrets
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, flash)

app = Flask(__name__)
app.secret_key = "shopis-secret-2024"

# Кэширование статики
@app.after_request
def add_headers(response):
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=604800'
    return response

DB_PATH = os.path.join(os.path.dirname(__file__), "shop.db")

STATUS_LABELS = {
    "pending":   "Ожидает",
    "confirmed": "Подтверждён",
    "shipped":   "Отправлен",
    "delivered": "Доставлен",
    "cancelled": "Отменён",
}

@app.template_filter("status_label")
def status_label(s):
    return STATUS_LABELS.get(s, s)

# ── Password helpers (hashlib, vstroenyy v Python) ────────────
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h    = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"

def check_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split(":")
        return hashlib.sha256((salt + password).encode()).hexdigest() == h
    except Exception:
        return False

# ── DB ────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cur  = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            login     TEXT NOT NULL UNIQUE,
            password  TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone     TEXT NOT NULL,
            email     TEXT NOT NULL,
            role      TEXT NOT NULL DEFAULT 'customer',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            description TEXT,
            price       REAL NOT NULL CHECK(price >= 0),
            stock       INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
            image_url   TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS orders (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status     TEXT NOT NULL DEFAULT 'pending',
            total      REAL NOT NULL DEFAULT 0,
            comment    TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity   INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0)
        );
        CREATE INDEX IF NOT EXISTS idx_orders_user   ON orders(user_id);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_items_order   ON order_items(order_id);
    """)

    # Миграция: добавить image_url если не существует
    try:
        cur.execute("ALTER TABLE products ADD COLUMN image_url TEXT")
        conn.commit()
    except Exception:
        pass  # колонка уже есть

    cur.execute("SELECT id FROM users WHERE login = 'admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (login, password, full_name, phone, email, role) VALUES (?,?,?,?,?,?)",
            ("admin", hash_password("admin123"), "Администратор", "+7-000-000-0000", "admin@shop.local", "admin")
        )

    cur.execute("SELECT COUNT(*) as c FROM products")
    if cur.fetchone()["c"] == 0:
        cur.executemany(
            "INSERT INTO products (name, description, price, stock, image_url) VALUES (?,?,?,?,?)",
            [
                ("Ноутбук ProBook X1", "Мощный ноутбук для работы и учёбы", 79990, 15, "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=300&fit=crop"),
                ("Смартфон Galaxy S", "Флагманский смартфон с отличной камерой", 59990, 30, "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300&fit=crop"),
                ("Наушники SoundMax", "Беспроводные наушники с ANC", 8990, 50, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop"),
                ("Клавиатура MechType", "Механическая клавиатура для геймеров", 6990, 25, "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400&h=300&fit=crop"),
            ]
        )

    conn.commit()
    conn.close()
    print("[init] База данных готова.")

# ── Auth helpers ──────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Доступ запрещён.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

# ── Routes ────────────────────────────────────────────────────
@app.route("/")
def index():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        login     = request.form.get("login",     "").strip()
        password  = request.form.get("password",  "").strip()
        full_name = request.form.get("full_name", "").strip()
        phone     = request.form.get("phone",     "").strip()
        email     = request.form.get("email",     "").strip()

        errors = {}
        if not login:     errors["login"]     = "Логин обязателен"
        if not password:  errors["password"]  = "Пароль обязателен"
        if not full_name: errors["full_name"] = "ФИО обязательно"
        if not phone:     errors["phone"]     = "Телефон обязателен"
        if not email:     errors["email"]     = "Email обязателен"

        if not errors:
            conn = get_db()
            cur  = conn.cursor()
            cur.execute("SELECT id FROM users WHERE login = ?", (login,))
            if cur.fetchone():
                errors["login"] = "Логин уже занят"
            else:
                cur.execute(
                    "INSERT INTO users (login, password, full_name, phone, email) VALUES (?,?,?,?,?)",
                    (login, hash_password(password), full_name, phone, email)
                )
                conn.commit()
                user_id = cur.lastrowid
                session.update({"user_id": user_id, "login": login,
                                "full_name": full_name, "role": "customer"})
                conn.close()
                flash("Регистрация успешна!", "success")
                return redirect(url_for("dashboard"))
            conn.close()
        return render_template("register.html", errors=errors, form=request.form)
    return render_template("register.html", errors={}, form={})

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_val = request.form.get("login",    "").strip()
        password  = request.form.get("password", "").strip()
        errors    = {}
        if not login_val: errors["login"]    = "Введите логин"
        if not password:  errors["password"] = "Введите пароль"

        if not errors:
            conn = get_db()
            cur  = conn.cursor()
            cur.execute("SELECT * FROM users WHERE login = ?", (login_val,))
            user = cur.fetchone()
            conn.close()
            if user and check_password(password, user["password"]):
                session.update({"user_id": user["id"], "login": user["login"],
                                "full_name": user["full_name"], "role": user["role"]})
                return redirect(url_for("admin_panel") if user["role"] == "admin"
                                else url_for("dashboard"))
            errors["general"] = "Неверный логин или пароль"
        return render_template("login.html", errors=errors, form=request.form)
    return render_template("login.html", errors={}, form={})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
        "SELECT id, status, total, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],)
    )
    orders = cur.fetchall()
    cur.execute("SELECT * FROM products WHERE stock > 0 ORDER BY name")
    products = cur.fetchall()
    conn.close()
    return render_template("dashboard.html", orders=orders, products=products)

@app.route("/order/new", methods=["POST"])
@login_required
def new_order():
    product_id = request.form.get("product_id")
    comment    = request.form.get("comment", "")
    try:
        quantity = int(request.form.get("quantity", 1))
        if quantity < 1: raise ValueError
    except ValueError:
        flash("Некорректное количество.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id = ? AND stock >= ?", (product_id, quantity))
    product = cur.fetchone()
    if not product:
        flash("Товар недоступен или закончился.", "error")
        conn.close()
        return redirect(url_for("dashboard"))

    total = product["price"] * quantity
    cur.execute(
        "INSERT INTO orders (user_id, status, total, comment) VALUES (?,?,?,?)",
        (session["user_id"], "pending", total, comment)
    )
    order_id = cur.lastrowid
    cur.execute(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?,?,?,?)",
        (order_id, product_id, quantity, product["price"])
    )
    cur.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
    conn.commit()
    conn.close()
    flash("Заказ успешно оформлен!", "success")
    return redirect(url_for("dashboard"))

@app.route("/admin")
@login_required
@admin_required
def admin_panel():
    conn = get_db()
    cur  = conn.cursor()
    status_filter = request.args.get("status", "")
    if status_filter:
        cur.execute(
            "SELECT o.id, o.status, o.total, o.created_at, o.comment, u.full_name, u.login "
            "FROM orders o JOIN users u ON o.user_id = u.id "
            "WHERE o.status = ? ORDER BY o.created_at DESC", (status_filter,)
        )
    else:
        cur.execute(
            "SELECT o.id, o.status, o.total, o.created_at, o.comment, u.full_name, u.login "
            "FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC"
        )
    orders = cur.fetchall()
    conn.close()
    statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    return render_template("admin.html", orders=orders,
                           statuses=statuses, current_filter=status_filter)

@app.route("/admin/order/<int:order_id>/status", methods=["POST"])
@login_required
@admin_required
def update_status(order_id):
    new_status = request.form.get("status")
    if new_status not in STATUS_LABELS:
        return "Bad status", 400
    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
        "UPDATE orders SET status = ?, updated_at = datetime('now') WHERE id = ?",
        (new_status, order_id)
    )
    conn.commit()
    conn.close()
    flash(f"Status zakaza #{order_id}: {STATUS_LABELS.get(new_status, new_status)}", "success")
    return redirect(url_for("admin_panel", status=request.args.get("status", "")))

@app.route("/api/check-login")
def check_login():
    login = request.args.get("login", "").strip()
    if not login:
        return jsonify({"available": False})
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE login = ?", (login,))
    taken = cur.fetchone() is not None
    conn.close()
    return jsonify({"available": not taken})

if __name__ == "__main__":
    init_db()
    print("\n  ShopIS запущен: http://localhost:5000")
    print("  Логин: admin / Пароль: admin123\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
