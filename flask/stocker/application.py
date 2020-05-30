#Import libraries and custom fuctions for the website
import os
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from flask_wtf import Form
from wtforms import DateField
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import apology, login_required,password_check

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#Data Base
db = SQL("sqlite:///stock.db")

# @app.route("/")
# def index():
#     "Show log in"
#     return render_template("login.html")

@app.route("/")
@login_required
def index():
    #show inventory transactions
    inventorys = db.execute("""SELECT dp.code, dp.name, sum(p.quantity) as quantity, u.alias \n
                    FROM ft_product p LEFT JOIN dim_product dp ON (p.product_id=dp.id) \n
                    LEFT JOIN dim_users u on (u.id=p.user_id) \n
                    GROUP BY 1,2,4""")

    return render_template("index.html", inventorys=inventorys)

@app.route("/register", methods=["GET", "POST"])
def register():
    #Register users
    #return apology("TODO")
    if request.method == "GET":
        return render_template("register.html")
    else:
        us_name = db.execute("SELECT * FROM dim_users WHERE username = :username",
                          username=request.form.get("username"))
        if len(us_name)>0:
            return apology("Username already exists", 403)
        elif not password_check(request.form.get("password")):
            return apology("check your password", 403)

        alias_name = db.execute("SELECT * FROM dim_users WHERE alias = :alias",
                          alias=request.form.get("alias"))
        if len(alias_name)>0:
            return apology("Alias already exists", 403)

        register_user = db.execute("INSERT INTO dim_users (username,hash) VALUES(:username,:hash)",
                          username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")))
        new_user = db.execute("SELECT * FROM dim_users WHERE username = :username",
                          username=request.form.get("username"))
        session["user_id"] = new_user[0]["id"]
        return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM dim_users WHERE username = lower(:username)",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/input", methods=["GET", "POST"])
@login_required
def input_():
    #Render template
    if request.method == "GET":
        return render_template("input.html")
    else:
        #Get available products
        code_prod = db.execute("SELECT * FROM dim_product WHERE code = :code",
                          code=request.form.get("code"))
        #Error if pass product does not exist
        if len(code_prod)<=0:
            return apology("Product Code does not already exists", 403)
        code_input = str(request.form.get("code"))
        q_input = int(request.form.get("quantity"))
        product_id = db.execute("SELECT id FROM dim_product WHERE code=:code", code=code_input)
        insert_q = db.execute("INSERT INTO ft_product (product_id,quantity,type,price_buy,price_sale,date) VALUES(:product_id,:quantity,:type,:price_buy,:price_sale,:date)",
                          product_id=product_id[0].get("id"), quantity=q_input, type='purchase',
                          price_buy=0,price_sale=0,date=datetime.datetime.now())
        return redirect("/")

@app.route("/output", methods=["GET", "POST"])
@login_required
def output():

    #Get available products to sell
    if request.method == "GET":
        products = db.execute("SELECT p.id, p.product_id, dp.code as code, dp.name, SUM(p.quantity) as quantity FROM ft_product p LEFT JOIN dim_product dp ON (p.product_id=dp.id)") #WHERE user_id=:id_user GROUP BY user_id, symbol, name", id_user=session["user_id"])
        return render_template("output.html", products=products)
    else:
        #Sell product and send that
        #data to the db
        code_prod = db.execute("SELECT * FROM dim_product WHERE code = :code",
                          code=request.form.get("code"))
        if len(code_prod)<=0:
            return apology("Product Code does not already exists", 403)

        code_input = str(request.form.get("code"))
        q_stock = db.execute("SELECT sum(p.quantity) as quantity FROM ft_product p LEFT JOIN dim_product dp ON (p.product_id=dp.id) WHERE dp.code=:code", code=code_input)
        q_output = int(request.form.get("quant_prod"))

        if q_output > q_stock[0]["quantity"]:
            return apology("NOT ENOUGH PRODUCTS", 400)

        product_id = db.execute("SELECT dp.id as id FROM dim_product dp WHERE dp.code=:code", code=code_input)

        #Pass sells as negative inputs
        q_output_neg = -1 * q_output

        update_q = db.execute("INSERT INTO ft_product (product_id,quantity,type,price_buy,price_sale,date) VALUES(:product_id,:quantity,:type,:price_buy,:price_sale,:date)",
                          product_id=product_id[0].get("id"), quantity=q_output_neg, type='sale',
                          price_buy=0,price_sale=0,date=datetime.datetime.now())
        return redirect("/")

@app.route("/newProduct", methods=["GET", "POST"])
@login_required
def new():

    #Create new products in the db
    if request.method == "GET":
        return render_template("newProduct.html")
    else:
        code_prod = db.execute("SELECT * FROM dim_product WHERE code = :code",
                          code=request.form.get("code"))
        if len(code_prod)>0:
            return apology("Product Code already exists", 403)

        #Add the new product to the db
        register_user = db.execute("INSERT INTO dim_product (code,name,create_time) VALUES(:code,:name,:date_insert)",
                            code=request.form.get("code"), name=request.form.get("name_prod"), date_insert=datetime.datetime.now())
        return redirect("/")

@app.route("/history/<string:code>")
@login_required
def history(code):
    #Show the history of certain product
    #All the sells and buys that product has had
    product=code#request.values.get('name')# form.get("username")
    print(product)
    inventorys = db.execute("""SELECT dp.code, dp.name, (case when p.quantity < 0 then 0 else p.quantity end) as bought,\n
                            (case when p.quantity < 0 then p.quantity else 0 end) as sold, date(p.date) as date FROM ft_product p\n
                            LEFT JOIN dim_product dp ON (p.product_id=dp.id)\n
                            WHERE dp.code = :product""",product=product)

    return render_template("history.html", inventorys=inventorys)

@app.route("/logout")
def logout():
    #Logout
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/analytics", methods=["GET", "POST"])
@login_required
def analytics():

    #Show graph to be have an analytics of the business
    if request.method == "GET":
        #data = list(db.execute("SELECT (quantity * (-1)) as quantity FROM ft_product where quantity < 0"))
        # datos = list(db.execute("select product_id, sum(quantity * (-1)) as quantity,strftime('%Y%m',date) as date from ft_product group by strftime('%Y-%m',date), product_id having quantity < 0"))
        #Retrieve data from the db
        datos = list(db.execute("""select dp.name as name, sum(ft.quantity * (-1)) as quantity,strftime('%Y-%m',ft.date) as date\n
                                from ft_product ft left join dim_product dp on (ft.product_id=dp.id)\n
                                group by strftime('%Y-%m',date), product_id having quantity < 0"""))
        #"select strftime('%Y',date) as "Year",strftime('%m',date) as "Month",strftime('%Y-%m',date) as "Year-month" from ft_product"
        prod = list(db.execute("SELECT code FROM dim_product"))
        prod_1 = db.execute("SELECT name FROM dim_product where id = 1")
        # sells = [d['quantity'] for d in datos]
        # date = [int(d['date']) for d in datos]

        # for d in prod:
        #     d['']

        prod_dict = {'1':{'sell':[23, 15, 177] , 'date': [202003, 202004, 202005]}}

        sells = prod_dict['1']['sell']
        date = prod_dict['1']['date']
        #Pass the data to the graph
        return render_template("analytics.html", sells=sells,date=date,produtos=prod,prod_l=prod_1[0]['name'])

    else:
        #Change product in the graph
        datos = list(db.execute("""select dp.name as name, sum(ft.quantity * (-1)) as quantity,strftime('%Y%m',ft.date) as date \n
                                from ft_product ft left join dim_product dp on (ft.product_id=dp.id) \n
                                group by strftime('%Y-%m',ft.date), ft.product_id having quantity < 0 and dp.code = :code"""
                                ,code=request.form.get("code")))

        prod = list(db.execute("SELECT code FROM dim_product"))

        prod_1 = db.execute("SELECT name FROM dim_product where code in (:code)",code=request.form.get("code"))

        sells = [d['quantity'] for d in datos]
        date = [int(d['date']) for d in datos]
        #Render new graph for the new requested product
        return render_template("analytics.html", sells=sells,date=date,produtos=prod,prod_l=prod_1[0]['name'])