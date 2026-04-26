from flask_login import UserMixin
from utils import get_db

class User(UserMixin):
    def __init__(self, row):
        self.id = row['UserID']
        self.username = row['Username']
        self.status = row['Status']

def load_user(user_id):
    db = get_db()
    row = db.execute("SELECT * FROM Users WHERE UserID=?", (user_id,)).fetchone()
    return User(row) if row else None
