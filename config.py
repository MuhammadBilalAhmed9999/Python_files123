import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecretkey'
    DATABASE = os.path.join(BASE_DIR, 'database', 'ProjectDB.db')
    WTF_CSRF_ENABLED = True

BUS_CATEGORY_LAYOUTS = {
    "Mini Bus": {"rows": 10, "cols": 2},
    "Standard": {"rows": 20, "cols": 2},
    "Luxury": {"rows": 10, "cols": 3},
    "Sleeper": {"rows": 12, "cols": 1},
}
