from flask import Flask, render_template, request, redirect, session
from modules.db_config import create_tables
from modules.auth import register_user, login_user
from modules.admin import add_product, add_market, add_daily_price, get_products, get_markets, delete_product, delete_market, get_all_price_records, delete_price
from modules.analysis import get_all_prices, get_best_buy_sell, calculate_percentage_change
from modules.prediction import generate_price_chart, predict_tomorrow_price, calculate_profit_estimation
from modules.alerts import generate_alerts
from modules.user_pref import save_preferred_product, get_user_preference

app = Flask(__name__)
app.secret_key = "smartmarketsecretkey"

create_tables()


# ================= HOME =================
@app.route('/')
def home():
    return render_template("index.html")


# ================= REGISTER =================
@app.route('/register')
def register():
    return render_template("register.html")


@app.route('/register_user', methods=['POST'])
def register_user_route():
    fullname = request.form['fullname']
    email = request.form['email']
    password = request.form['password']

    success = register_user(fullname, email, password)

    if success:
        return redirect('/login')
    else:
        return "Email already exists!"


# ================= LOGIN =================
@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/login_user', methods=['POST'])
def login_user_route():
    email = request.form['email']
    password = request.form['password']

    user = login_user(email, password)

    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['fullname']
        session['role'] = user['role']

        if user['role'] == 'admin':
            return redirect('/admin')
        else:
            return redirect('/dashboard')
    else:
        return "Invalid Email or Password"


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ================= SAVE USER PREFERENCE =================
@app.route('/save_preference', methods=['POST'])
def save_preference():
    product_id = request.form['preferred_product']
    save_preferred_product(session['user_id'], product_id)
    return redirect('/dashboard')


# ================= USER DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    products = get_products()
    preferred_product = get_user_preference(session['user_id'])

    prices = []
    best_buy = None
    best_sell = None
    percentage_change = 0
    tomorrow_price = 0
    estimated_profit = 0
    alert_message = "Select product"

    if preferred_product:
        prices = get_all_prices(preferred_product)
        best_buy, best_sell = get_best_buy_sell(preferred_product)
        percentage_change = calculate_percentage_change(preferred_product)
        generate_price_chart(preferred_product)
        tomorrow_price = predict_tomorrow_price(preferred_product)
        estimated_profit = calculate_profit_estimation(preferred_product)
        alert_message = generate_alerts(preferred_product)

    return render_template("dashboard.html",
                           name=session['user_name'],
                           products=products,
                           preferred_product=preferred_product,
                           prices=prices,
                           best_buy=best_buy,
                           best_sell=best_sell,
                           tomorrow_price=tomorrow_price,
                           estimated_profit=estimated_profit,
                           percentage_change=percentage_change,
                           alert_message=alert_message)


# ================= ADMIN DASHBOARD =================
@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect('/login')

    products = get_products()
    markets = get_markets()
    prices = get_all_price_records()

    return render_template("admin_dashboard.html",
                           name=session['user_name'],
                           products=products,
                           markets=markets,
                           prices=prices)

# ================= ADD PRODUCT =================
@app.route('/add_product')
def add_product_page():
    if 'user_id' not in session:
        return redirect('/login')

    return render_template("add_product.html")


@app.route('/save_product', methods=['POST'])
def save_product():
    product_name = request.form['product_name']
    add_product(product_name)
    return redirect('/admin')


# ================= ADD MARKET =================
@app.route('/add_market')
def add_market_page():
    if 'user_id' not in session:
        return redirect('/login')

    return render_template("add_market.html")


@app.route('/save_market', methods=['POST'])
def save_market():
    market_name = request.form['market_name']
    location = request.form['location']
    distance = request.form['distance']
    add_market(market_name, location, distance)
    return redirect('/admin')


# ================= ADD DAILY PRICE =================
@app.route('/add_price')
def add_price_page():
    if 'user_id' not in session:
        return redirect('/login')

    products = get_products()
    markets = get_markets()
    return render_template("add_price.html", products=products, markets=markets)


@app.route('/save_price', methods=['POST'])
def save_price():
    product_id = request.form['product_id']
    market_id = request.form['market_id']
    price = request.form['price']
    price_date = request.form['price_date']
    add_daily_price(product_id, market_id, price, price_date)
    return redirect('/admin')

@app.route('/delete_product/<int:id>')
def remove_product(id):
    delete_product(id)
    return redirect('/admin')


@app.route('/delete_market/<int:id>')
def remove_market(id):
    delete_market(id)
    return redirect('/admin')


@app.route('/delete_price/<int:id>')
def remove_price(id):
    delete_price(id)
    return redirect('/admin')


if __name__ == "__main__":
    app.run(debug=True)