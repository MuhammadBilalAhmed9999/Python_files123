import sqlite3
from flask import g, current_app
from flask_login import current_user

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def has_permission(permission_name):
    # single-role admin model: any logged-in user with role Admin => all access
    if not current_user.is_authenticated:
        return False
    db = get_db()
    row = db.execute("SELECT 1 FROM UserRoles ur JOIN Roles r ON ur.RoleID=r.RoleID WHERE ur.UserID=? AND r.RoleName='Admin'", (current_user.id,)).fetchone()
    return row is not None

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
