import sqlite3
from werkzeug.security import generate_password_hash
from config import Config

# CHANGE THESE VALUES
USERNAME = "Bilal"
PASSWORD = "Bilal123"
STATUS = "Active"   # or "Inactive"


def create_user():
    db_path = Config.DATABASE

    password_hash = generate_password_hash(
        PASSWORD,
        method="pbkdf2:sha256",
        salt_length=16
    )

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO Users (Username, PasswordHash, Status)
            VALUES (?, ?, ?)
        """, (USERNAME, password_hash, STATUS))

        conn.commit()

        print("✅ User created successfully")
        print("Username:", USERNAME)
        print("Status:", STATUS)

    except sqlite3.IntegrityError as e:
        print("❌ Failed to create user (already exists?)")
        print(e)

    finally:
        conn.close()


if __name__ == "__main__":
    create_user()
