from flask import Flask, render_template, url_for, request, redirect, flash, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from collections import defaultdict
from datetime import datetime
from flask_restful import Api, Resource, reqparse, abort
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from sqlalchemy.sql import func
import requests
import csv
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)
api = Api(app)

app.config['SECRET_KEY'] = 'hjshjhdjahkjshkjdhjs'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'

db = SQLAlchemy(app)

# auth = Blueprint('auth', __name__)

class User(db.Model, UserMixin):
     __tablename__ = 'Users'
     id             = db.Column(db.Integer, primary_key=True)
     email          = db.Column(db.String(150), unique=True)
     password       = db.Column(db.String(150))
     first_name     = db.Column(db.String(150))

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        new_email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=new_email).first()
        if user:
            if check_password_hash(user.password, password):
                #flash('Logged in successfully!', category='success')
                #login_user(user, remember=True)
                return redirect("/products/")
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')
            
    return render_template("login.html", user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/login/")

@app.route('/sign-up/', methods=["GET", "POST"])
def sign_up():
    if request.method == 'POST':
        new_email = request.form.get('email')
        new_first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email = new_email).first()

        if user:
            flash('Email already exists.', category='error')
        elif len(new_email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(new_first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email = new_email, first_name = new_first_name, password = generate_password_hash(password1,method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            #flash('Account created!', category='success')
            #login_user(user, remember=True)
            return redirect("/")
        
    return render_template("sign_up.html")

class Storage(db.Model):
    __tablename__ = 'storage'
    ID = db.Column(db.Integer, primary_key=True)
    Category_ID = db.Column(db.Integer)
    #Name = db.Column(db.String(49))

    def __repr__(self):
        return '<Storage %r>' % self.ID


class Food_item(db.Model):
    __tablename__ = 'food_items'
    ID = db.Column(db.Integer, primary_key=True)
    Category_ID = db.Column(db.Integer)
    Name = db.Column(db.String(49))
    Name_subtitle = db.Column(db.String(112))
    DOP_Pantry_Max = db.Column(db.Integer)
    DOP_Refrigerate_Max = db.Column(db.Integer)
    DOP_Refrigerate_Metric = db.Column(db.String(6))
    # Refrigerate_After_Opening_Max = db.Column(db.Integer)
    # Refrigerate_After_Opening_Metric = db.Column(db.String(15))

    def __repr__(self):
        return '<Food_item %r>' % self.ID
    
    def __eq__(self, other):
        if isinstance(other, Food_item):
            return self.Name == other.Name
        return NotImplemented

    def __hash__(self):
        return hash(self.Name)


class Product(db.Model):

    __tablename__ = 'products'
    product_id      = db.Column(db.String(200), primary_key=True)
    #quantity        = db.Column(db.Integer)
    date_created    = db.Column(db.DateTime, default=datetime.utcnow)
    production_date = db.Column(db.Date)
    use_by = db.Column(db.Date)
    storage = db.Column(db.Integer)

    #user_id         = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Product %r>' % self.product_id

class Location(db.Model):
    __tablename__   = 'locations'
    location_id     = db.Column(db.String(200), primary_key=True)
    date_created    = db.Column(db.DateTime, default=datetime.utcnow)
    capacity_m3     = db.Column(db.Integer)
    storage_c       = db.Column(db.Integer)
    available_space_m3 = db.Column(db.Integer)
    
    def __repr__(self):
        return '<Location %r>' % self.location_id

class ProductMovement(db.Model):
    __tablename__   = 'productmovements'
    movement_id     = db.Column(db.Integer, primary_key=True)
    product_id      = db.Column(db.Integer, db.ForeignKey('products.product_id'))
    qty             = db.Column(db.Integer)
    from_location   = db.Column(db.Integer, db.ForeignKey('locations.location_id'))
    to_location     = db.Column(db.Integer, db.ForeignKey('locations.location_id'))
    movement_time   = db.Column(db.DateTime, default=datetime.utcnow)

    product         = db.relationship('Product', foreign_keys=product_id)
    fromLoc         = db.relationship('Location', foreign_keys=from_location)
    toLoc           = db.relationship('Location', foreign_keys=to_location)
    
    def __repr__(self):
        return '<ProductMovement %r>' % self.movement_id

@app.route('/', methods=["POST", "GET"])
def index():
        
    if (request.method == "POST") and ('product_name' in request.form):
        product_name    = request.form["product_name"]
        new_product     = Product(product_id=product_name)

        # production_date    = request.form["production_date"]
        # use_by    = request.form["use_by"]
        # storage    = request.form["storage"]

        
        # product_name    = request.form["product_name"]
        # new_production = Product(product_id=product_name)
        # use_by = db.Column(db.Date)
        # storage = db.Column(db.Integer)

        try:
            db.session.add(new_product)
            db.session.commit()
            return redirect("/")
        
        except:
            return "There Was an issue while add a new Product"
    
    if (request.method == "POST") and ('location_name' in request.form):
        location_name    = request.form["location_name"]
        new_location     = Location(location_id=location_name)

        try:
            db.session.add(new_location)
            db.session.commit()
            return redirect("/")
        
        except:
            return "There Was an issue while add a new Location"
    else:
        products    = Product.query.order_by(Product.date_created).all()
        locations   = Location.query.order_by(Location.date_created).all()
        return render_template("index.html", products = products, locations = locations, user = current_user)

@app.route('/locations/', methods=["POST", "GET"])
def viewLocation():
    if (request.method == "POST") and ('location_name' in request.form):
        location_name = request.form["location_name"]
        new_capacity = request.form["loc_capacity"]
        new_storage  = request.form["loc_storage"]
        new_location = Location(location_id=location_name, capacity_m3 = new_capacity, storage_c = new_storage)

        try:
            db.session.add(new_location)
            db.session.commit()
            return redirect("/locations/")

        except:
            locations = Location.query.order_by(Location.date_created).all()
            return "There Was an issue while add a new Location"
    else:
        locations = Location.query.order_by(Location.date_created).all()
        return render_template("locations.html", locations=locations)

# Custom JSON Encoder for Food_item objects
class FoodItemEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Food_item):
            return {"ID": obj.ID, "Category_ID": obj.Category_ID, "Name": obj.Name, "Name_subtitle": obj.Name_subtitle}
        return super().default(obj)
    
@app.route('/products/', methods=["POST", "GET"])
def viewProduct():
    food_items = Food_item.query.all()
    #food_items
    unique_items = list(set(food_items))
    unique_items = sorted(unique_items, key=lambda x: x.Name)

    food_json = {}
    for food_item in food_items:
        if food_item.Name not in food_json:
            food_json[food_item.Name] = {"Category_ID": food_item.Category_ID, "Name": food_item.Name, "products": []}
            #template konstravimas i weba
        food_json[food_item.Name]["products"].append({"Name_subtitle":food_item.Name_subtitle,"DOP_Refrigerate_Max":food_item.DOP_Refrigerate_Max,"DOP_Refrigerate_Metric":food_item.DOP_Refrigerate_Metric})
            #print(food_json)
        # food_json[food_item.Name]["products"].append(json.loads(json.dumps(food_item)))
    #print(food_json)
    #unique_food_items = list({item.Name for item in food_items})

    if (request.method == "POST") and ('product_name' in request.form):
        product_name = request.form["product_name"]
        production = request.form["production_date"]
        production = datetime.strptime(production, '%Y-%m-%d').date()
        new_use_by = request.form["use_by"]
        new_use_by = datetime.strptime(new_use_by, '%Y-%m-%d').date()
        new_storage = request.form["storage"]
        # new_product = Product(product_id= product_name, storage = new_storage, production_date = production, use_by = new_use_by)
        new_product = Product(product_id= product_name, production_date = production, use_by = new_use_by, storage = new_storage )
         
    #      product_id      = db.Column(db.String(200), primary_key=True)
    # #quantity        = db.Column(db.Integer)
    # date_created    = db.Column(db.DateTime, default=datetime.utcnow)
    # production_date = db.Column(db.Date)
    # use_by = db.Column(db.Date)
    # storage = db.Column(db.Integer)
        try:
            db.session.add(new_product)
            db.session.commit()
            return redirect("/products/")

        except:
            #products = Product.query.order_by(Product.date_created).all()
            #db.session.rollback()
            return "There Was an issue while add a new Product"
    else:
        products = Product.query.order_by(Product.date_created).all()
        #unique_items
        #food_items = unique_items
        #food_items= food_items_json
        # Serialize food_items to JSON format using our custom encoder
        #food_items_json = json.dumps(unique_items, cls=FoodItemEncoder)
        #print(food_json)
        #loaded_JSON = json.loads(food_items_json)
        #food_items= loaded_JSON
        #len= len(loaded_JSON)
        #food_items = food_json
        return render_template("products.html", products=products, food_items = food_json)

@app.route("/update-product/<name>", methods=["POST", "GET"])
def updateProduct(name):
    product = Product.query.get_or_404(name)
    old_porduct = product.product_id

    if request.method == "POST":
        product.product_id    = request.form['product_name']
        

        try:
            db.session.commit()
            updateProductInMovements(old_porduct, request.form['product_name'])
            return redirect("/products/")

        except:
            return "There was an issue while updating the Product"
    else:
        return render_template("update-product.html", product=product)

@app.route("/delete-product/<name>")
def deleteProduct(name):
    product_to_delete = Product.query.get_or_404(name)

    try:
        db.session.delete(product_to_delete)
        db.session.commit()
        return redirect("/products/")
    except:
        return "There was an issue while deleteing the Product"

@app.route("/update-location/<name>", methods=["POST", "GET"])
def updateLocation(name):
    location = Location.query.get_or_404(name)
    old_location = location.location_id

    if request.method == "POST":
        location.location_id = request.form['location_name']

        try:
            db.session.commit()
            updateLocationInMovements(
                old_location, request.form['location_name'])
            return redirect("/locations/")

        except:
            return "There was an issue while updating the Location"
    else:
        return render_template("update-location.html", location=location)

@app.route("/delete-location/<name>")
def deleteLocation(name):
    location_to_delete = Location.query.get_or_404(name)

    try:
        db.session.delete(location_to_delete)
        db.session.commit()
        return redirect("/locations/")
    except:
        return "There was an issue while deleting the Location"

@app.route("/movements/", methods=["POST", "GET"])
def viewMovements():
    if request.method == "POST" :
        product_id      = request.form["productId"]
        qty             = request.form["qty"]
        fromLocation    = request.form["fromLocation"]
        toLocation      = request.form["toLocation"]
        new_movement = ProductMovement(
            product_id=product_id, qty=qty, from_location=fromLocation, to_location=toLocation)

        try:
            db.session.add(new_movement)
            db.session.commit()
            return redirect("/movements/")

        except:
            return "There Was an issue while add a new Movement"
    else:
        products    = Product.query.order_by(Product.date_created).all()
        locations   = Location.query.order_by(Location.date_created).all()
        movs = ProductMovement.query\
        .join(Product, ProductMovement.product_id == Product.product_id)\
        .add_columns(
            ProductMovement.movement_id,
            ProductMovement.qty,
            Product.product_id,
            #Product.quantity, 
            ProductMovement.from_location,
            ProductMovement.to_location,
            ProductMovement.movement_time)\
        .all()

        movements   = ProductMovement.query.order_by(
            ProductMovement.movement_time).all()
        return render_template("movements.html", movements=movs, products=products, locations=locations)

@app.route("/update-movement/<int:id>", methods=["POST", "GET"])
def updateMovement(id):

    movement    = ProductMovement.query.get_or_404(id)
    products    = Product.query.order_by(Product.date_created).all()
    locations   = Location.query.order_by(Location.date_created).all()

    if request.method == "POST":
        movement.product_id  = request.form["productId"]
        movement.qty         = request.form["qty"]
        movement.from_location= request.form["fromLocation"]
        movement.to_location  = request.form["toLocation"]

        try:
            db.session.commit()
            return redirect("/movements/")

        except:
            return "There was an issue while updating the Product Movement"
    else:
        return render_template("update-movement.html", movement=movement, locations=locations, products=products)

@app.route("/delete-movement/<int:id>")
def deleteMovement(id):
    movement_to_delete = ProductMovement.query.get_or_404(id)

    try:
        db.session.delete(movement_to_delete)
        db.session.commit()
        return redirect("/movements/")
    except:
        return "There was an issue while deleteing the Prodcut Movement"

@app.route("/product-balance/", methods=["POST", "GET"])
def productBalanceReport():
    movs = ProductMovement.query.\
        join(Product, ProductMovement.product_id == Product.product_id).\
        add_columns(
            Product.product_id, 
            ProductMovement.qty,
            ProductMovement.from_location,
            ProductMovement.to_location,
            ProductMovement.movement_time).\
        order_by(ProductMovement.product_id).\
        order_by(ProductMovement.movement_id).\
        all()
    balancedDict = defaultdict(lambda: defaultdict(dict))
    tempProduct = ''
    for mov in movs:
        row = mov[0]
        if(tempProduct == row.product_id):
            if(row.to_location and not "qty" in balancedDict[row.product_id][row.to_location]):
                balancedDict[row.product_id][row.to_location]["qty"] = 0
            elif (row.from_location and not "qty" in balancedDict[row.product_id][row.from_location]):
                balancedDict[row.product_id][row.from_location]["qty"] = 0
            if (row.to_location and "qty" in balancedDict[row.product_id][row.to_location]):
                balancedDict[row.product_id][row.to_location]["qty"] += row.qty
            if (row.from_location and "qty" in balancedDict[row.product_id][row.from_location]):
                balancedDict[row.product_id][row.from_location]["qty"] -= row.qty
            pass
        else :
            tempProduct = row.product_id
            if(row.to_location and not row.from_location):
                if(balancedDict):
                    balancedDict[row.product_id][row.to_location]["qty"] = row.qty
                else:
                    balancedDict[row.product_id][row.to_location]["qty"] = row.qty

    return render_template("product-balance.html", movements=balancedDict)

@app.route("/movements/get-from-locations/", methods=["POST"])
def getLocations():
    product = request.form["productId"]
    location = request.form["location"]
    locationDict = defaultdict(lambda: defaultdict(dict))
    locations = ProductMovement.query.\
        filter( ProductMovement.product_id == product).\
        filter(ProductMovement.to_location != '').\
        add_columns(ProductMovement.from_location, ProductMovement.to_location, ProductMovement.qty).\
        all()

    for key, location in enumerate(locations):
        if(locationDict[location.to_location] and locationDict[location.to_location]["qty"]):
            locationDict[location.to_location]["qty"] += location.qty
        else:
            locationDict[location.to_location]["qty"] = location.qty

    return locationDict


@app.route("/dub-locations/", methods=["POST", "GET"])
def getDublicate():
    location = request.form["location"]
    locations = Location.query.\
        filter(Location.location_id == location).\
        all()
    print(locations)
    if locations:
        return {"output": False}
    else:
        return {"output": True}

@app.route("/dub-products/", methods=["POST", "GET"])
def getPDublicate():
    product_name = request.form["product_name"]
    products = Product.query.\
        filter(Product.product_id == product_name).\
        all()
    print(products)
    if products:
        return {"output": False}
    else:
        return {"output": True}

def updateLocationInMovements(oldLocation, newLocation):
    movement = ProductMovement.query.filter(ProductMovement.from_location == oldLocation).all()
    movement2 = ProductMovement.query.filter(ProductMovement.to_location == oldLocation).all()
    for mov in movement2:
        mov.to_location = newLocation
    for mov in movement:
        mov.from_location = newLocation
     
    db.session.commit()

def updateProductInMovements(oldProduct, newProduct):
    movement = ProductMovement.query.filter(ProductMovement.product_id == oldProduct).all()
    for mov in movement:
        mov.product_id = newProduct
    
    db.session.commit()

# def find_food_by_name(food_name):

#     # Call the USDA Foodkeeper API to get the database of food items
#     response = requests.get('https://www.fsis.usda.gov/shared/data/EN/foodkeeper.json')
#     data = response.json()

#     # Search for the food item by name
#     found_items = []
#     for item in data:
#         if 'name' in item and food_name.lower() in item['name'].lower():
#             found_items.append(item)

#     return found_items

# @app.route('/convert')
# def convert_csv_to_sqlite():

@app.route('/convert')
def convert_csv_to_sqlite():
    # Set up a connection to the database
    conn = sqlite3.connect('inventory.db') 

    # Set up a cursor object to execute SQL commands
    cursor = conn.cursor()

    # Create a new table in the database
    cursor.execute('''CREATE TABLE food_items
                    (id INTEGER PRIMARY KEY, Category_ID INTEGER, Name TEXT, Name_subtitle TEXT, Pantry_Min INTEGER, 
                    Pantry_Max INTEGER, Pantry_Metric TEXT, Pantry_tips TEXT, DOP_Pantry_Min INTEGER, DOP_Pantry_Max INTEGER,
                        DOP_Pantry_Metric TEXT, DOP_Pantry_tips TEXT, Pantry_After_Opening_Min TEXT, Pantry_After_Opening_Max TEXT,
                        Pantry_After_Opening_Metric TEXT, )''')

if (__name__ == "__main__"):
    #starts the application
    app.run(debug=True)

# @auth.route('/login/', methods=['POST'])
# def login():
#     if request.method == 'POST':
#         new_email = request.form.get('email')
#         password = request.form.get('password')

#         user = User.query.filter_by(email=new_email).first()
#         if user:
#             if check_password_hash(user.password, password):
#                 #flash('Logged in successfully!', category='success')
#                 login_user(user, remember=True)
#                 return redirect("https://www.youtube.com/")
#             else:
#                 flash('Incorrect password, try again.', category='error')
#         else:
#             flash('Email does not exist.', category='error')
            
#     return render_template("login.html", user=current_user)