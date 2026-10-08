
-- Demo data for the online shop


-- Categories
INSERT INTO categories (name) VALUES
    ('Electronics'),
    ('Books'),
    ('Home & Kitchen'),
    ('Sports');

-- Products
INSERT INTO products (name, category_id, price, stock) VALUES
    ('Wireless Mouse',        1,  29.99, 150),
    ('Mechanical Keyboard',   1,  89.50,  60),
    ('USB-C Cable 2m',        1,   9.99, 400),
    ('Clean Code (book)',     2,  34.00,  45),
    ('The Pragmatic Programmer', 2, 39.95, 30),
    ('Coffee Mug',            3,   7.50, 200),
    ('Non-stick Pan',         3,  24.00,  80),
    ('Yoga Mat',              4,  19.99,  70),
    ('Dumbbell Set 10kg',     4,  59.00,  25);

-- Customers
INSERT INTO customers (full_name, email, city) VALUES
    ('Alice Martin',   'alice@example.com',   'Paris'),
    ('Bob Chen',       'bob@example.com',     'Berlin'),
    ('Clara Dubois',   'clara@example.com',   'Lyon'),
    ('David Kumar',    'david@example.com',   'Mumbai'),
    ('Elena Rossi',    'elena@example.com',   'Rome');

-- Orders
INSERT INTO orders (customer_id, product_id, quantity, total, order_date) VALUES
    (1, 1, 2,  59.98, '2026-09-01'),
    (1, 4, 1,  34.00, '2026-09-01'),
    (2, 2, 1,  89.50, '2026-09-05'),
    (3, 6, 3,  22.50, '2026-09-08'),
    (4, 9, 1,  59.00, '2026-09-12'),
    (5, 8, 2,  39.98, '2026-09-15'),
    (2, 3, 4,  39.96, '2026-09-18'),
    (3, 5, 1,  39.95, '2026-09-20');