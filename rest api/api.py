from flask import Flask,request,jsonify,make_response,session
import uuid
from werkzeug.security import generate_password_hash,check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import datetime


app = Flask(__name__)

# Configurations
app.config['SECRET_KEY'] = "secretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:@localhost/review"

# SQLAlchemy Instance
db = SQLAlchemy(app)


# Models
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    publicid = db.Column(db.String(250),unique=True)
    name = db.Column(db.String(50),nullable=False)
    password = db.Column(db.String(250))
    contact=db.Column(db.String(10))
    email = db.Column(db.String(50))
    admin=db.Column(db.Boolean)
    creationdate=db.Column(db.DateTime,default=datetime.datetime.utcnow,nullable=False)
    updationdate=db.Column(db.DateTime,default=datetime.datetime.utcnow,nullable=False)
    enable=db.Column(db.Boolean)
    

class Restaurant(db.Model):
    __tablename__ = 'restaurant'
    restaurantid = db.Column(db.Integer, primary_key=True,autoincrement=True)
    restaurantpublicid = db.Column(db.String(250),unique=True)
    restaurantname = db.Column(db.String(50),nullable=False)
    restaurantaddress = db.Column(db.String(60),nullable=False)
    restaurantcontact = db.Column(db.String(10))
    restaurantemail = db.Column(db.String(20))
    restaurantrating = db.Column(db.Float)
    restaurantimage = db.Column(db.String(50))
    restaurantmenu = db.Column(db.String(50)) 
    avgcost = db.Column(db.Integer)
    updationdate = db.Column(db.DateTime,default=datetime.datetime.utcnow,nullable=False)
    creationdate = db.Column(db.DateTime,default=datetime.datetime.utcnow,nullable=False)


class Review(db.Model):
    __tablename__ = 'review'
    reviewid = db.Column(db.Integer,primary_key=True,autoincrement=True)
    reviewtext = db.Column(db.String(300),nullable=False)
    responsetext = db.Column(db.String(300))
    isreplied = db.Column(db.Boolean)
    postdate= db.Column(db.DateTime,default=datetime.datetime.utcnow,nullable=False)
    userpublicid = db.Column(db.String(50), ForeignKey('user.publicid')) 
    user = relationship("User", back_populates="review")
    restaurantpublicid = db.Column(db.String(50), ForeignKey('restaurant.restaurantpublicid')) 
    restaurant = relationship("Restaurant", back_populates="review")


class Template(db.Model):
    __tablename__ = 'template'
    templateid = db.Column(db.Integer,primary_key=True,autoincrement=True)
    templatetext = db.Column(db.String(200))
    sentimentscore = db.Column(db.Integer)


# Mappings 
User.review = relationship("Review", order_by=Review.reviewid, back_populates="user")
Restaurant.review = relationship("Review", order_by=Review.reviewid, back_populates="restaurant")


# Routes
@app.route("/")
def home():
    return "hello app"    


@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('email',None)
    session.pop('publicid',None)
    return jsonify({'message':'logout'})


@app.route('/register' , methods=['POST'])
def register_user():
    print("register user")
    data = request.get_json(force=True)
    print("data: "+str(data))
    hashed_password = generate_password_hash(data['password'] , method='sha256')
    new_user = User(publicid=str(uuid.uuid4()),name=data['name'],password=hashed_password,contact=data['contact'],email=data['email'],admin=False,enable=True)
    print("here")
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message':"user created"})



@app.route('/login' , methods=['POST'])
def login():
    data = request.get_json(force=True)
    if not data :
        return jsonify('Could not verify')
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify('Could not verify')        

    print("pass compare: ",check_password_hash(user.password,data['password']))
    if check_password_hash(user.password,data['password']):
        print("pass compare: ",user.password," ",data['password'])
        session['username'] = user.name
        session['email'] = user.email
        session['publicid'] = user.publicid
        return jsonify({"message": "login Successfull"})
    
    return jsonify({"message": "Password incorrect"})




@app.route('/getuser/<publicid>',methods=['GET'])
def get_user(publicid):
    print("public id: ",publicid)
    user = User.query.filter_by(publicid=publicid).first()

    if not user:
        return jsonify({'message' : 'No user found!'})
    
    user_data = {}
    user_data['publicid'] = user.publicid
    user_data['name'] = user.name
    user_data['admin'] = user.admin
    user_data['contact'] = user.contact
    user_data['email'] = user.email
    
    return jsonify({'user' : user_data })



@app.route('/addrestaurant' , methods=['POST'])
def add_restaurant():
    data = request.get_json(force=True)
    new_restaurant = Restaurant(restaurantpublicid=str(uuid.uuid4()),restaurantname=data['name'],restaurantaddress=data['address'],restaurantcontact=data['contact'],restaurantemail=data['email'],
    restaurantrating=data['rating'],restaurantimage=data['image'],restaurantmenu=data['menu'],avgcost=data['cost'])
    db.session.add(new_restaurant)
    db.session.commit()

    return jsonify({'message':"Restaurant added"})



@app.route('/getallrestaurants' , methods=['GET'])
def get_all_restaurants():
    restaurants=Restaurant.query.all()
    if not restaurants:
        return jsonify({'message' : 'No restaurant found!'})
    restaurants_data=[]
    for restaurant in restaurants:
        restaurant_data={}
        restaurant_data['restaurantpublicid'] = restaurant.restaurantpublicid
        restaurant_data['restaurantname'] = restaurant.restaurantname
        restaurant_data['restaurantaddress'] = restaurant.restaurantaddress
        restaurant_data['restaurantcontact'] = restaurant.restaurantcontact
        restaurant_data['restaurantemail'] = restaurant.restaurantemail
        restaurant_data['restaurantrating'] = restaurant.restaurantrating
        restaurant_data['restaurantimage'] = restaurant.restaurantimage
        restaurant_data['restaurantmenu'] = restaurant.restaurantmenu
        restaurant_data['avgcost'] = restaurant.avgcost
        
        restaurants_data.append(restaurant_data)

    return jsonify({'restaurants' : restaurants_data})


@app.route('/getrestaurant/<restaurant_id>' , methods=['GET'])
def get_restaurant(restaurant_id):
    restaurant=Restaurant.query.filter_by(restaurantpublicid=restaurant_id).first()
    if not restaurant:
        return jsonify({'message' : 'No restaurant found!'})
    
    restaurant_data={}
    restaurant_data['restaurantpublicid'] = restaurant.restaurantpublicid
    restaurant_data['restaurantname'] = restaurant.restaurantname
    restaurant_data['restaurantaddress'] = restaurant.restaurantaddress
    restaurant_data['restaurantcontact'] = restaurant.restaurantcontact
    restaurant_data['restaurantemail'] = restaurant.restaurantemail
    restaurant_data['restaurantrating'] = restaurant.restaurantrating
    restaurant_data['restaurantimage'] = restaurant.restaurantimage
    restaurant_data['restaurantmenu'] = restaurant.restaurantmenu
    restaurant_data['avgcost'] = restaurant.avgcost

    return jsonify({'restaurant' : restaurant_data})

@app.route('/postreview/<restaurant_id>',methods=['POST'])
def post_review(restaurant_id):
    





if __name__ == "__main__":
    app.run(debug=True)