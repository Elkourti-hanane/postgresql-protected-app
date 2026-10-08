"""
Task 3 — Interactive CRUD app for the online shop database.
Config loading, table/column whitelist, DB connection, and menu.
"""
import os
import sys
import getpass
import yaml
import psycopg2

# ------------------------------------------------------------------
# 1. Load trusted connection settings from the config file,
#    with optional env var overrides (host / port / database).
# ------------------------------------------------------------------
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")

with open(CONFIG_PATH, "r") as f:
    config_from_file = yaml.safe_load(f)

ALLOWED_CONFIG_KEYS = {"host", "port", "database", "sslmode", "connect_timeout"}
safe_config = {k: v for k, v in config_from_file.items()
               if k in ALLOWED_CONFIG_KEYS}

if os.environ.get("DB_HOST"):
    safe_config["host"] = os.environ["DB_HOST"]
if os.environ.get("DB_PORT"):
    safe_config["port"] = int(os.environ["DB_PORT"])
if os.environ.get("DB_NAME"):
    safe_config["database"] = os.environ["DB_NAME"]

# ------------------------------------------------------------------
# 2. Whitelist of tables and columns (SECURITY: prevents SQL injection
#    through identifiers, which cannot be parameterized)
# ------------------------------------------------------------------
ALLOWED_TABLES = {
    "categories": {"id", "name"},
    "products":   {"id", "name", "category_id", "price", "stock"},
    "customers":  {"id", "full_name", "email", "city"},
    "orders":     {"id", "customer_id", "product_id",
                   "quantity", "total", "order_date"},
}

UPDATABLE_COLUMNS = {
    "categories": {"name"},
    "products":   {"name", "category_id", "price", "stock"},
    "customers":  {"full_name", "email", "city"},
    "orders":     {"customer_id", "product_id",
                   "quantity", "total", "order_date"},
}

def check_table(table: str) -> str:
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Unknown table: {table}")
    return table

def check_column(table: str, column: str) -> str:
    if column not in ALLOWED_TABLES[table]:
        raise ValueError(f"Unknown column '{column}' for table '{table}'")
    return column

# ------------------------------------------------------------------
# 3. Connect using trusted config + user-provided credentials
# ------------------------------------------------------------------
def get_connection():
    user = input("DB login: ").strip()
    password = getpass.getpass("DB password: ")

    return psycopg2.connect(
        host=safe_config["host"],
        port=safe_config["port"],
        dbname=safe_config["database"],
        sslmode=safe_config.get("sslmode", "prefer"),
        connect_timeout=safe_config.get("connect_timeout", 5),
        user=user,
        password=password,
    )

# ------------------------------------------------------------------
# 4. Feature: list all rows of a table (no filter)
# ------------------------------------------------------------------
def list_all(conn, table: str):
    table = check_table(table)
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {table};")
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description]

    if not rows:
        print(f"(no rows in {table})")
        return

    print(" | ".join(columns))
    print("-" * (len(" | ".join(columns))))
    for row in rows:
        print(" | ".join(str(v) for v in row))
    print(f"\n{len(rows)} row(s).")

# ------------------------------------------------------------------
# 5. Feature: filter by one column
# ------------------------------------------------------------------
def filter_one(conn, table: str, column: str, value: str):
    table = check_table(table)
    column = check_column(table, column)

    sql = f"SELECT * FROM {table} WHERE {column} = %s;"

    with conn.cursor() as cur:
        cur.execute(sql, (value,))
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description]

    if not rows:
        print("(no matching rows)")
        return

    print(" | ".join(columns))
    print("-" * (len(" | ".join(columns))))
    for row in rows:
        print(" | ".join(str(v) for v in row))
    print(f"\n{len(rows)} row(s).")

def show_table_columns(table: str):
    """Print the whitelisted columns for a table."""
    table = check_table(table)
    print(f"Available columns in '{table}':")
    print("  " + ", ".join(sorted(ALLOWED_TABLES[table])))

# ------------------------------------------------------------------
# 6. Feature: filter by MULTIPLE columns (AND)
# ------------------------------------------------------------------
def filter_many(conn, table: str, conditions: list):
    table = check_table(table)

    if not conditions:
        raise ValueError("No conditions provided")

    checked = [(check_column(table, c), v) for c, v in conditions]
    where_clause = " AND ".join(f"{col} = %s" for col, _ in checked)
    values = tuple(v for _, v in checked)

    sql = f"SELECT * FROM {table} WHERE {where_clause};"

    with conn.cursor() as cur:
        cur.execute(sql, values)
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description]

    if not rows:
        print("(no matching rows)")
        return

    print(" | ".join(columns))
    print("-" * (len(" | ".join(columns))))
    for row in rows:
        print(" | ".join(str(v) for v in row))
    print(f"\n{len(rows)} row(s).")

# ------------------------------------------------------------------
# 7. Feature: update ONE row by id
# ------------------------------------------------------------------
def update_one(conn, table: str, row_id: str, changes: list):
    table = check_table(table)

    if not changes:
        raise ValueError("No changes provided")

    seen = set()
    checked = []
    for col, val in changes:
        if col in seen:
            raise ValueError(f"Duplicate column '{col}' in changes")
        seen.add(col)
        if col not in UPDATABLE_COLUMNS[table]:
            raise ValueError(f"Column '{col}' is not updatable in '{table}'")
        checked.append((col, val))

    set_clause = ", ".join(f"{col} = %s" for col, _ in checked)
    values = [v for _, v in checked]
    values.append(row_id)

    sql = f"UPDATE {table} SET {set_clause} WHERE id = %s;"

    with conn.cursor() as cur:
        cur.execute(sql, values)
        affected = cur.rowcount
    conn.commit()

    print(f"{affected} row(s) updated.")

# ------------------------------------------------------------------
# 8. Feature: update MANY rows, setting a common value for a group
# ------------------------------------------------------------------
def update_many(conn, table: str, set_column: str, new_value: str,
                where_column: str, where_values: list):
    table = check_table(table)

    if set_column not in UPDATABLE_COLUMNS[table]:
        raise ValueError(f"Column '{set_column}' is not updatable in '{table}'")
    where_column = check_column(table, where_column)

    if not where_values:
        raise ValueError("No values provided for the WHERE IN clause")

    placeholders = ", ".join(["%s"] * len(where_values))
    sql = (
        f"UPDATE {table} "
        f"SET {set_column} = %s "
        f"WHERE {where_column} IN ({placeholders});"
    )

    params = [new_value] + where_values

    with conn.cursor() as cur:
        cur.execute(sql, params)
        affected = cur.rowcount
    conn.commit()

    print(f"{affected} row(s) updated.")

# ------------------------------------------------------------------
# 9. Feature: insert ONE row into a table
# ------------------------------------------------------------------
def insert_one(conn, table: str, values: dict):
    table = check_table(table)

    if not values:
        raise ValueError("No values provided")

    for col in values.keys():
        if col not in ALLOWED_TABLES[table]:
            raise ValueError(f"Unknown column '{col}' for table '{table}'")
        if col == "id":
            raise ValueError("Column 'id' is auto-generated; do not insert it")

    cols = ", ".join(values.keys())
    placeholders = ", ".join(["%s"] * len(values))
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) RETURNING id;"

    with conn.cursor() as cur:
        cur.execute(sql, list(values.values()))
        new_id = cur.fetchone()[0]
    conn.commit()

    print(f"Inserted 1 row into {table}. New id = {new_id}.")

# ------------------------------------------------------------------
# 10. Feature: insert into TWO related tables (parent + child)
# ------------------------------------------------------------------
def insert_two_related(conn, parent_table: str, parent_values: dict,
                       child_table: str, child_values: dict,
                       child_fk_col: str):
    parent_table = check_table(parent_table)
    child_table = check_table(child_table)

    if not parent_values or not child_values:
        raise ValueError("Both parent and child values are required")

    if child_fk_col not in ALLOWED_TABLES[child_table]:
        raise ValueError(
            f"Unknown FK column '{child_fk_col}' in '{child_table}'"
        )
    if child_fk_col in child_values:
        raise ValueError(
            f"Do not include '{child_fk_col}' in child values — "
            f"it is filled from parent id"
        )

    for col in parent_values.keys():
        if col not in ALLOWED_TABLES[parent_table] or col == "id":
            raise ValueError(f"Invalid parent column '{col}'")
    for col in child_values.keys():
        if col not in ALLOWED_TABLES[child_table] or col == "id":
            raise ValueError(f"Invalid child column '{col}'")

    p_cols = ", ".join(parent_values.keys())
    p_placeholders = ", ".join(["%s"] * len(parent_values))
    parent_sql = (
        f"INSERT INTO {parent_table} ({p_cols}) "
        f"VALUES ({p_placeholders}) RETURNING id;"
    )

    c_cols = ", ".join(list(child_values.keys()) + [child_fk_col])
    c_placeholders = ", ".join(["%s"] * (len(child_values) + 1))
    child_sql = (
        f"INSERT INTO {child_table} ({c_cols}) "
        f"VALUES ({c_placeholders}) RETURNING id;"
    )

    try:
        with conn.cursor() as cur:
            cur.execute(parent_sql, list(parent_values.values()))
            parent_id = cur.fetchone()[0]

            child_params = list(child_values.values()) + [parent_id]
            cur.execute(child_sql, child_params)
            child_id = cur.fetchone()[0]

        conn.commit()
        print(
            f"Inserted into {parent_table} (new id={parent_id}) "
            f"and {child_table} (new id={child_id}, "
            f"{child_fk_col}={parent_id})."
        )
    except Exception:
        conn.rollback()
        raise

# ------------------------------------------------------------------
# 11. Helper: read N column/value pairs, rejecting duplicates
# ------------------------------------------------------------------
def read_pairs(n: int, label: str):
    """Ask the user for `n` (column, value) pairs. Return a dict.
    If a column is repeated, abort and return None."""
    values = {}
    for i in range(n):
        col = input(f"  {label} column #{i+1}: ").strip()
        if col in values:
            print(f"Error: column '{col}' already entered", file=sys.stderr)
            return None
        val = input(f"  {label} value  #{i+1}: ").strip()
        values[col] = val
    return values

# ------------------------------------------------------------------
# 12. Menu loop
# ------------------------------------------------------------------
MENU = """
--- Online Shop CRUD ---
Available tables: categories, products, customers, orders
1) List all rows of a table
2) Filter by one column
3) Filter by multiple columns (AND)
4) Update one row by id
5) Update many rows (set one value for a group)
6) Insert one row
7) Insert one row into two related tables
0) Exit
Choose an option: """

WELCOME = """
==================================================
   Online Shop CRUD  -  Task 3
   Development of Protected Software
   WELCOME!
==================================================
"""

GOODBYE = """
  Thanks for using the Online Shop CRUD  
    Have a great day! 
"""

def main():
    print(WELCOME)
    try:
        conn = get_connection()
    except Exception as e:
        print(f"Connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("Connected. Enjoy! \n")

    try:
        while True:
            try:
                choice = input(MENU).strip()
            except (KeyboardInterrupt, EOFError):
                print(GOODBYE)
                break

            if choice == "0":
                print(GOODBYE)
                break

            elif choice == "1":
                table = input(
                    "Table name (categories/products/customers/orders): "
                ).strip()
                try:
                    list_all(conn, table)
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)

            elif choice == "2":
                table = input(
                    "Table name (categories/products/customers/orders): "
                ).strip()
                try:
                    show_table_columns(table)
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                    continue

                column = input("Column name: ").strip()
                value = input("Value to match: ").strip()
                try:
                    filter_one(conn, table, column, value)
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)

            elif choice == "3":
                table = input(
                    "Table name (categories/products/customers/orders): "
                ).strip()
                try:
                    show_table_columns(table)
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                    continue

                n = input("How many conditions? (e.g. 2): ").strip()
                try:
                    n = int(n)
                    if n < 1:
                        raise ValueError("Number must be at least 1")
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                    continue

                conditions = []
                seen = set()
                dup = False
                for i in range(n):
                    col = input(f"  Column #{i+1} (name): ").strip()
                    if col in seen:
                        print(f"Error: column '{col}' already entered",
                              file=sys.stderr)
                        dup = True
                        break
                    seen.add(col)
                    val = input(f"  Value  #{i+1} (to match): ").strip()
                    conditions.append((col, val))

                if dup:
                    continue

                try:
                    filter_many(conn, table, conditions)
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)

            elif choice == "4":
                table = input(
                    "Table name (categories/products/customers/orders): "
                ).strip()
                try:
                    show_table_columns(table)
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                    continue

                row_id = input("Row id to update: ").strip()
                n = input("How many columns to change? ").strip()
                try:
                    n = int(n)
                    if n < 1:
                        raise ValueError("At least 1")
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                    continue

                changes = []
                seen = set()
                dup = False
                for i in range(n):
                    col = input(f"  Column #{i+1} (name): ").strip()
                    if col in seen:
                        print(f"Error: column '{col}' already entered",
                              file=sys.stderr)
                        dup = True
                        break
                    seen.add(col)
                    val = input(f"  New value #{i+1}: ").strip()
                    changes.append((col, val))

                if dup:
                    continue

                try:
                    update_one(conn, table, row_id, changes)
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                except Exception as e:
                    conn.rollback()
                    print(f"Update failed: {e}", file=sys.stderr)

            elif choice == "5":
                table = input(
                    "Table name (categories/products/customers/orders): "
                ).strip()
                try:
                    show_table_columns(table)
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                    continue

                set_col = input("Column to SET: ").strip()
                new_val = input("New value: ").strip()
                where_col = input("WHERE column: ").strip()
                vals = input(
                    "WHERE values (comma-separated): "
                ).strip()
                where_values = [v.strip() for v in vals.split(",") if v.strip()]

                try:
                    update_many(conn, table, set_col, new_val,
                                where_col, where_values)
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                except Exception as e:
                    conn.rollback()
                    print(f"Update failed: {e}", file=sys.stderr)

            elif choice == "6":
                table = input(
                    "Table name (categories/products/customers/orders): "
                ).strip()
                try:
                    show_table_columns(table)
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                    continue

                n = input("How many columns to insert? ").strip()
                try:
                    n = int(n)
                    if n < 1:
                        raise ValueError("At least 1")
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                    continue

                values = read_pairs(n, "")
                if values is None:
                    continue

                try:
                    insert_one(conn, table, values)
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                except Exception as e:
                    conn.rollback()
                    print(f"Insert failed: {e}", file=sys.stderr)

            elif choice == "7":
                parent = input("Parent table: ").strip()
                child  = input("Child table: ").strip()
                fk     = input("FK column in child that points to parent: ").strip()

                try:
                    pn = int(input("How many parent columns? ").strip())
                except ValueError:
                    print("Error: enter a number", file=sys.stderr)
                    continue

                parent_values = read_pairs(pn, "Parent")
                if parent_values is None:
                    continue

                try:
                    cn = int(input(
                        "How many child columns? (not counting FK) "
                    ).strip())
                except ValueError:
                    print("Error: enter a number", file=sys.stderr)
                    continue

                child_values = read_pairs(cn, "Child")
                if child_values is None:
                    continue

                try:
                    insert_two_related(conn, parent, parent_values,
                                       child, child_values, fk)
                except ValueError as e:
                    print(f"Error: {e}", file=sys.stderr)
                except Exception as e:
                    conn.rollback()
                    print(f"Insert failed: {e}", file=sys.stderr)

            else:
                print("Unknown option.", file=sys.stderr)

    finally:
        conn.close()

# ------------------------------------------------------------------
# 13. Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    main()