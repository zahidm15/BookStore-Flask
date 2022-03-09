import hashlib
import os
import sqlite3

from flask import *
from werkzeug.utils import secure_filename

from constants import DB_PATH, UPLOAD_FOLDER
from login import get_login_details, is_valid
from utils import parse, allowed_file

app = Flask(__name__)
app.secret_key = 'random string'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/")
def root():
    logged_in, first_name, no_of_items = get_login_details()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock, ISBN FROM products')
        item_data = cur.fetchall()
        cur.execute('SELECT categoryId, name FROM categories')
        category_data = cur.fetchall()
    item_data = parse(item_data)
    return render_template('home.html', itemData=item_data,
                           loggedIn=logged_in,
                           firstName=first_name,
                           noOfItems=no_of_items,
                           categoryData=category_data)


@app.route("/add")
def admin():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT categoryId, name FROM categories")
        categories = cur.fetchall()
    conn.close()
    return render_template('add.html', categories=categories)


@app.route("/addItem", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])
        category_id = int(request.form['category'])
        isbn = int(request.form['ISBN'])

        # Uploading image procedure
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_name = filename
        with sqlite3.connect(DB_PATH) as conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    '''INSERT INTO products (name, price, description, image, stock, categoryId, ISBN) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (name, price, description, image_name, stock, category_id, isbn))
                conn.commit()
                msg = "added successfully"
            except:
                msg = "error occurred"
                conn.rollback()
        conn.close()
        print(msg)
        return redirect(url_for('root'))


@app.route("/remove")
def remove():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock ISBN FROM products')
        data = cur.fetchall()
    conn.close()
    return render_template('remove.html', data=data)


@app.route("/removeItem")
def remove_item():
    product_id = request.args.get('productId')
    with sqlite3.connect(DB_PATH) as conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM products WHERE productID = ' + product_id)
            conn.commit()
            msg = "Deleted successfully"
        except:
            conn.rollback()
            msg = "Error occurred"
    conn.close()
    print(msg)
    return redirect(url_for('root'))


@app.route("/displayCategory")
def display_category():
    logged_in, first_name, no_of_items = get_login_details()
    category_id = request.args.get("categoryId")
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT products.productId, products.name, products.price, products.image, products.ISBN, categories.name FROM products, categories WHERE products.categoryId = categories.categoryId AND categories.categoryId = " + category_id)
        data = cur.fetchall()
    conn.close()
    category_name = data[0][4]
    data = parse(data)
    return render_template('displayCategory.html', data=data, loggedIn=logged_in, firstName=first_name,
                           noOfItems=no_of_items, categoryName=category_name)


@app.route("/account/profile")
def profile_home():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = get_login_details()
    return render_template("profileHome.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)


@app.route("/account/profile/edit")
def edit_profile():
    if 'email' not in session:
        return redirect(url_for('root'))
    logged_in, first_name, no_of_items = get_login_details()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT userId, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone FROM users WHERE email = '" +
            session['email'] + "'")
        profileData = cur.fetchone()
    conn.close()
    return render_template("editProfile.html", profileData=profileData, loggedIn=logged_in, firstName=first_name,
                           noOfItems=no_of_items)


@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def change_password():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    if request.method == "POST":
        old_password = request.form['oldpassword']
        old_password = hashlib.md5(old_password.encode()).hexdigest()
        new_password = request.form['newpassword']
        new_password = hashlib.md5(new_password.encode()).hexdigest()
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId, password FROM users WHERE email = '" + session['email'] + "'")
            user_id, password = cur.fetchone()
            if password == old_password:
                try:
                    cur.execute("UPDATE users SET password = ? WHERE userId = ?", (new_password, user_id))
                    conn.commit()
                    msg = "Changed successfully"
                except:
                    conn.rollback()
                    msg = "Failed"
                return render_template("changePassword.html", msg=msg)
            else:
                msg = "Wrong password"
        conn.close()
        return render_template("changePassword.html", msg=msg)
    else:
        return render_template("changePassword.html")


@app.route("/updateProfile", methods=["GET", "POST"])
def update_profile():
    if request.method == 'POST':
        email = request.form['email']
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        with sqlite3.connect(DB_PATH) as con:
            try:
                cur = con.cursor()
                cur.execute(
                    'UPDATE users SET firstName = ?, lastName = ?, address1 = ?, address2 = ?, zipcode = ?, city = ?, state = ?, country = ?, phone = ? WHERE email = ?',
                    (first_name, last_name, address1, address2, zipcode, city, state, country, phone, email))

                con.commit()
                msg = "Saved Successfully"
            except:
                con.rollback()
                msg = "Error occured"
        con.close()
        return redirect(url_for('edit_profile'))


@app.route("/loginForm")
def loginForm():
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html', error='')


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid UserId / Password'
            return render_template('login.html', error=error)


@app.route("/productDescription")
def productDescription():
    logged_in, first_name, no_of_items = get_login_details()
    product_id = request.args.get('productId')
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT productId, name, price, description, image, stock, ISBN FROM products WHERE productId = ' + product_id)
        product_data = cur.fetchone()
    conn.close()
    return render_template("productDescription.html", data=product_data, loggedIn=logged_in, firstName=first_name,
                           noOfItems=no_of_items)


@app.route("/addToCart")
def add_to_cart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    else:
        product_id = int(request.args.get('productId'))
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = '" + session['email'] + "'")
            user_id = cur.fetchone()[0]
            try:
                cur.execute("INSERT INTO cart (userId, productId) VALUES (?, ?)", (user_id, product_id))
                conn.commit()
                msg = "Added successfully"
            except:
                conn.rollback()
                msg = "Error occured"
        conn.close()
        return redirect(url_for('root'))


@app.route("/cart")
def cart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    logged_in, first_name, no_of_items = get_login_details()
    email = session['email']
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        cur.execute(
            "SELECT products.productId, products.name, products.price, products.image FROM products, cart WHERE products.productId = cart.productId AND cart.userId = " + str(
                userId))
        product = cur.fetchall()
    shipment = 0
    postage = 3
    for row in product:
        if row[1] == 1:

            shipment = postage
        elif row[2] > 1:
            shipment = postage + 1
    total_price = shipment
    for row in product:
        total_price += row[2]
    return render_template("cart.html", product=product, postage=shipment, totalPrice=total_price, loggedIn=logged_in,
                           firstName=first_name, noOfItems=no_of_items)


@app.route("/removeFromCart")
def remove_from_cart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session['email']
    productId = int(request.args.get('productId'))
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        try:
            cur.execute("DELETE FROM cart WHERE userId = " + str(userId) + " AND productId = " + str(productId))
            conn.commit()
            msg = "removed successfully"
        except:
            conn.rollback()
            msg = "error occured"
    conn.close()
    return redirect(url_for('root'))


@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))


@app.route("/checkout", methods=['GET', 'POST'])
def payment():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    logged_in, first_name, no_of_items = get_login_details()
    email = session['email']

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        cur.execute(
            "SELECT products.productId, products.name, products.price, products.image FROM products, cart WHERE products.productId = cart.productId AND cart.userId = " + str(
                userId))
        product = cur.fetchall()
    total_price = 0
    for row in product:
        total_price += row[2]
        print(row)
        cur.execute("INSERT INTO orders (userId, productId) VALUES (?, ?)", (userId, row[0]))
    cur.execute("DELETE FROM cart WHERE userId = " + str(userId))
    conn.commit()

    return render_template("checkout.html", product=product, totalPrice=total_price, loggedIn=logged_in,
                           firstName=first_name, noOfItems=no_of_items)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Parse form data
        password = request.form['password']
        email = request.form['email']
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']

        with sqlite3.connect(DB_PATH) as con:
            try:
                cur = con.cursor()
                cur.execute(
                    'INSERT INTO users (password, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (
                    hashlib.md5(password.encode()).hexdigest(), email, first_name, last_name, address1, address2, zipcode,
                    city, state, country, phone))

                con.commit()

                msg = "Registered Successfully"
            except:
                con.rollback()
                msg = "Error occured"
        con.close()
        return render_template("login.html", error=msg)


@app.route("/registerationForm")
def registration_form():
    return render_template("register.html")


if __name__ == '__main__':
    app.run(debug=True)
