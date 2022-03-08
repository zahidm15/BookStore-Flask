import sqlite3

from flask import session

from constants import DB_PATH


def getLoginDetails():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        if 'email' not in session:
            loggedIn = False
            firstName = ''
            noOfItems = 0
        else:
            loggedIn = True
            cur.execute("SELECT userId, firstName FROM users WHERE email = '" + session['email'] + "'")
            userId, firstName = cur.fetchone()
            cur.execute("SELECT count(productId) FROM cart WHERE userId = " + str(userId))
            noOfItems = cur.fetchone()[0]
    conn.close()
    return loggedIn, firstName, noOfItems