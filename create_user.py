"""
Run this script to create a new user:
  python3 create_user.py
"""
import mysql.connector
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import getpass
import os

def main():
    """Gets user input and creates a new user in the database."""
    load_dotenv()

    username = input("Enter username: ").strip()
    # Use getpass to hide password entry for better security
    password = getpass.getpass("Enter password: ").strip()

    if not username or not password:
        print("❌ Username and password cannot be empty.")
        return

    hashed_password = generate_password_hash(password)

    db = None
    cursor = None
    try:
        db = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_password)
        )
        db.commit()
        print(f"✅ User '{username}' created successfully!")
    except mysql.connector.IntegrityError:
        print(f"❌ Username '{username}' already exists.")
    except mysql.connector.Error as err:
        print(f"❌ An error occurred: {err}")
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

if __name__ == "__main__":
    main()