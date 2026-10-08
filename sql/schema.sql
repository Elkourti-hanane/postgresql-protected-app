
-- Task 3 — Online Shop database schema
-- 4 related tables: categories, products, customers, orders


DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS categories CASCADE;


-- categories: product categories

CREATE TABLE categories (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(100) NOT NULL UNIQUE
);


-- products: items for sale, each belongs to a category

CREATE TABLE products (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(200) NOT NULL,
    category_id  INT NOT NULL REFERENCES categories(id),
    price        NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    stock        INT NOT NULL DEFAULT 0 CHECK (stock >= 0)
);

-- ------------------------------------------------------------
-- customers: buyers
-- ------------------------------------------------------------
CREATE TABLE customers (
    id         SERIAL PRIMARY KEY,
    full_name  VARCHAR(200) NOT NULL,
    email      VARCHAR(200) NOT NULL UNIQUE,
    city       VARCHAR(100)
);

-- ------------------------------------------------------------
-- orders: a customer buys a product
-- ------------------------------------------------------------
CREATE TABLE orders (
    id           SERIAL PRIMARY KEY,
    customer_id  INT NOT NULL REFERENCES customers(id),
    product_id   INT NOT NULL REFERENCES products(id),
    quantity     INT NOT NULL CHECK (quantity > 0),
    total        NUMERIC(10,2) NOT NULL CHECK (total >= 0),
    order_date   DATE NOT NULL DEFAULT CURRENT_DATE
);