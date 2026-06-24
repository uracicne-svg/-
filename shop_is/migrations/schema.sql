-- ============================================================
--  Shop IS  —  схема БД
--  PostgreSQL
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    login       VARCHAR(64)  NOT NULL UNIQUE,
    password    VARCHAR(256) NOT NULL,          -- bcrypt hash
    full_name   VARCHAR(128) NOT NULL,
    phone       VARCHAR(20)  NOT NULL,
    email       VARCHAR(128) NOT NULL,
    role        VARCHAR(16)  NOT NULL DEFAULT 'customer',  -- 'customer' | 'admin'
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(128) NOT NULL,
    description TEXT,
    price       NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    stock       INTEGER       NOT NULL DEFAULT 0 CHECK (stock >= 0),
    created_at  TIMESTAMP     NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status      VARCHAR(32) NOT NULL DEFAULT 'pending',
    -- statuses: pending | confirmed | shipped | delivered | cancelled
    total       NUMERIC(10,2) NOT NULL DEFAULT 0,
    comment     TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    id          SERIAL PRIMARY KEY,
    order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    quantity    INTEGER       NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0)
);

-- индексы
CREATE INDEX IF NOT EXISTS idx_orders_user   ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_items_order   ON order_items(order_id);

-- тестовый администратор (пароль: admin123)
-- bcrypt hash для 'admin123'
INSERT INTO users (login, password, full_name, phone, email, role)
VALUES (
    'admin',
    '$2b$12$KIX5kC2O1ZxRR1X.YP4iEeCAZqn2g4kHqVvVFDQ5LwCUoGAlM.lXi',
    'Администратор Системы',
    '+7-900-000-0000',
    'admin@shop.local',
    'admin'
) ON CONFLICT (login) DO NOTHING;

-- тестовые товары
INSERT INTO products (name, description, price, stock) VALUES
    ('Ноутбук ProBook X1',  'Мощный ноутбук для работы',      79990.00, 15),
    ('Смартфон Galaxy S',   'Флагманский смартфон',            59990.00, 30),
    ('Наушники SoundMax',   'Беспроводные наушники ANC',       8990.00,  50),
    ('Клавиатура MechType', 'Механическая клавиатура',         6990.00,  25)
ON CONFLICT DO NOTHING;
