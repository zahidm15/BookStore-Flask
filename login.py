import hashlib
import sqlite3

from flask import session

from constants import DB_PATH


def get_login_details() -> tuple[bool, str, int]:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        if 'email' not in session:
            logged_in = False
            first_name = ''
            no_of_items = 0
        else:
            logged_in = True
            cur.execute("SELECT userId, firstName FROM users WHERE email = '" + session['email'] + "'")
            userId, first_name = cur.fetchone()
            cur.execute("SELECT count(productId) FROM cart WHERE userId = " + str(userId))
            no_of_items = cur.fetchone()[0]
    conn.close()
    return logged_in, first_name, no_of_items


def is_valid(email, password):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('SELECT email, password FROM users')
    data = cur.fetchall()
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False