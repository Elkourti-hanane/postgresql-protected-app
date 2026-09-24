import yaml
import getpass
import psycopg2

# 1. Load trusted settings from the config file
import os
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")

with open(CONFIG_PATH, "r") as file:
    config_from_file = yaml.safe_load(file)

# 2. SECURITY: Whitelist only the allowed keys.
#    This prevents a malicious config file from adding extra options
#    like "options=-c ..." which could compromise the connection.
ALLOWED_KEYS = {"host", "port", "database", "sslmode"}
safe_connection_params = {
    key: value for key, value in config_from_file.items() if key in ALLOWED_KEYS
}

# 3. Get login and password FROM THE USER only.
#    We use getpass for the password so it doesn't show on screen.
user_login = input("Enter database login: ")
user_password = getpass.getpass("Enter database password: ")

# 4. Combine them safely. The user cannot inject extra options.
#    We call psycopg2.connect with explicit keyword arguments.
try:
    connection = psycopg2.connect(
        host=safe_connection_params["host"],
        port=safe_connection_params["port"],
        dbname=safe_connection_params["database"],
        sslmode=safe_connection_params.get("sslmode", "prefer"),
        user=user_login,
        password=user_password
    )

    # 5. Run the required query.
    cursor = connection.cursor()
    cursor.execute("SELECT VERSION();")
    db_version = cursor.fetchone()
    print("\nSuccessfully connected!")
    print(f"PostgreSQL Version: {db_version[0]}")

    # Clean up
    cursor.close()
    connection.close()

except psycopg2.Error as error:
    print(f"\nFailed to connect or run query: {error}")
