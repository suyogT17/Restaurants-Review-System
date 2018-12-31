from flask import Flask,request,jsonify,make_response,session
import uuid
from werkzeug.security import generate_password_hash,check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import datetime
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"//*": {"origins": "*"}})

# Configurations
app.config['SECRET_KEY'] = "secretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:@localhost/review"
app.config['JWT_SECRET_KEY'] = 'super-secret'
jwt = JWTManager(app)

# SQLAlchemy Instance
db = SQLAlchemy(app)


# Models
class Role(db.Model):
    __tablename__ = 'role'
    roleid = db.Column(db.Integer,primary_key=True,autoincrement=True)
    rolename = db.Column(db.Text())


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    publicid = db.Column(db.String(250),unique=True)
    name = db.Column(db.String(50),nullable=False)
    password = db.Column(db.String(250))
    contact=db.Column(db.String(10))
    email = db.Column(db.String(50))
    creationdate=db.Column(db.DateTime,default=datetime.datetime.utcnow,nullable=False)
    updationdate=db.Column(db.DateTime,default=datetime.datetime.utcnow,nullable=False)
    enable=db.Column(db.Boolean)
    roleid = db.Column(db.Integer, ForeignKey('role.roleid')) 
    role = relationship("Role", back_populates="user")
    

class Restaurant(db.Model):
    __tablename__ = 'restaurant'
    restaurantid = db.Column(db.Integer, primary_key=True,autoincrement=True)
    restaurantpublicid = db.Column(db.String(250),unique=True)
    restaurantname = db.Column(db.String(50),nullable=False)
    restaurantaddress = db.Column(db.Text(),nullable=False)
    restaurantcontact = db.Column(db.String(10))
    restaurantemail = db.Column(db.String(20))
    restaurantrating = db.Column(db.Float)
    restaurantimage = db.Column(db.String(50))
    restaurantmenu = db.Column(db.String(50)) 
    avgcost = db.Column(db.Integer)
    updationdate = db.Column(db.DateTime,default=datetime.datetime.utcnow,nullable=False)
    creationdate = db.Column(db.DateTime,default=datetime.datetime.utcnow,nullable=False)
    userpublicid = db.Column(db.String(250), ForeignKey('user.publicid')) 
    user = relationship("User", back_populates="restaurant")
    

class Review(db.Model):
    __tablename__ = 'review'
    reviewid = db.Column(db.Integer,primary_key=True,autoincrement=True)
    reviewtext = db.Column(db.Text(),nullable=False)
    responsetext = db.Column(db.Text())
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
User.restaurant = relationship("Restaurant", order_by=Restaurant.restaurantid, back_populates="user")
Restaurant.review = relationship("Review", order_by=Review.reviewid, back_populates="restaurant")
Role.user = relationship("User",order_by=User.id , back_populates="role")

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
    role = Role.query.filter_by(roleid=3).first()
    print("role.rolename")
    hashed_password = generate_password_hash(data['password'] , method='sha256')
    new_user = User(publicid=str(uuid.uuid4()),name=data['name'],password=hashed_password,contact=data['contact'],email=data['email'],enable=True,role=role)
    print("here")
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message':"user created"})



@app.route('/login' , methods=['POST'])
def login():
    data = request.get_json(force=True)
    if not data :
        return jsonify({"message": "Malformed Request Data"}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({"message": "User Not Found"}), 401      

    print("pass compare: ",check_password_hash(user.password,data['password']))
    if check_password_hash(user.password,data['password']):
        print("pass compare: ",user.password," ",data['password'])
        session['username'] = user.name
        session['email'] = user.email
        session['publicid'] = user.publicid
        message = {}
        message['message'] = "login Successfull"
        if user.roleid == 1:
            message['isadmin'] = True
            message['isowner'] = False
            message['restaurantpublicid'] = None
        elif user.roleid == 2:
            message['isadmin'] = False
            message['isowner'] = True
            restaurant = Restaurant.query.filter_by(userpublicid = user.publicid).first()
            message['restaurantpublicid'] = restaurant.restaurantpublicid
        else:
            message['isadmin'] = False
            message['isowner'] = False
            message['restaurantpublicid'] = None

        access_token = create_access_token(identity=user.publicid, expires_delta=False)
        message['access_token'] = access_token
        message['message'] = 'Login Success'
        return jsonify(message), 200
    
    return jsonify({"message": "Password incorrect"}), 401



@app.route('/getuser/<publicid>',methods=['GET'])
@jwt_required
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
@jwt_required

def add_restaurant():
    data = request.get_json(force=True)
    if not data:
        return jsonify("invalid request")
    owner = User.query.filter_by(publicid=data['owner']).first()
    # make owner 
    role = Role.query.filter_by(roleid=2).first()
    owner.role = role
    new_restaurant = Restaurant(restaurantpublicid=str(uuid.uuid4()),restaurantname=data['name'],restaurantaddress=data['address'],restaurantcontact=data['contact'],restaurantemail=data['email'],
    restaurantrating=data['rating'],restaurantimage=data['image'],restaurantmenu=data['menu'],avgcost=data['cost'],user=owner)
    db.session.add(new_restaurant)
    db.session.add(owner) #update
    db.session.commit()

    return jsonify({'message':"Restaurant added"})

@app.route('/static/<path:path>')
def static_file(path):
    return app.send_static_file(path)

@app.route('/getallrestaurants' , methods=['GET'])
# @jwt_required

def get_all_restaurants():
    restaurants=Restaurant.query.all()
    restaurants_data=[]
    if not restaurants:
        return jsonify(restaurants_data)
    for restaurant in restaurants:
        restaurant_data={}
        restaurant_data['publicid'] = restaurant.restaurantpublicid
        restaurant_data['name'] = restaurant.restaurantname
        restaurant_data['address'] = restaurant.restaurantaddress
        restaurant_data['contact'] = restaurant.restaurantcontact
        restaurant_data['email'] = restaurant.restaurantemail
        restaurant_data['rating'] = restaurant.restaurantrating
        restaurant_data['image'] = restaurant.restaurantimage
        restaurant_data['menu'] = restaurant.restaurantmenu
        restaurant_data['cost'] = restaurant.avgcost
        
        restaurants_data.append(restaurant_data)

    return jsonify(restaurants_data)


@app.route('/getrestaurant/<restaurant_id>' , methods=['GET'])
@jwt_required

def get_restaurant(restaurant_id):
    restaurant=Restaurant.query.filter_by(restaurantpublicid=restaurant_id).first()
    if not restaurant:
        return jsonify({'message' : 'No restaurant found!'})
    
    restaurant_data={}
    restaurant_data['publicid'] = restaurant.restaurantpublicid
    restaurant_data['name'] = restaurant.restaurantname
    restaurant_data['address'] = restaurant.restaurantaddress
    restaurant_data['contact'] = restaurant.restaurantcontact
    restaurant_data['email'] = restaurant.restaurantemail
    restaurant_data['rating'] = restaurant.restaurantrating
    restaurant_data['image'] = restaurant.restaurantimage
    restaurant_data['menu'] = restaurant.restaurantmenu
    restaurant_data['cost'] = restaurant.avgcost

    return jsonify(restaurant_data)

	
@app.route('/postreview',methods=['POST'])
@jwt_required

def post_review():
    data=request.get_json(force=True)
    # if 'publicid' in session:
    #     publicid=session['publicid']
    #     user = User.query.filter_by(publicid=publicid).first()
    # else:
    #     return jsonify("login to post review!")
    restaurant=Restaurant.query.filter_by(restaurantpublicid=data['restaurantid']).first()
    userid = get_jwt_identity()
    user = User.query.filter_by(publicid=userid).first()
    new_review=Review(reviewtext=data['reviewtext'],isreplied=False,user=user,restaurant=restaurant)
    db.session.add(new_review)
    db.session.commit()
    return jsonify({"message" : "review posted!"})


@app.route('/postresponse',methods=['POST'])
@jwt_required

def post_response():
    data=request.get_json(force=True)
    review = Review.query.filter_by(reviewid = data['reviewid']).first()
    if not review:
        return jsonify({"message" : "no review found"})
    review.responsetext = data['responsetext']
    message = ''
    if review.isreplied:
        message = 'response edited successfully'
    else:
        review.isreplied = True
        message = 'response posted successfully'
    
    db.session.add(review)
    db.session.commit()
    return jsonify({"message" : message })

    
    
    



@app.route('/getreviews/<public_id>',methods=['GET'])
@jwt_required

def get_review(public_id):
    reviews=Review.query.filter_by(restaurantpublicid=public_id)
    
    if not reviews:
        return jsonify({"message" : "no reviews!"})
    reviews_data=[]
    for review in reviews:
        review_data={}
        review_data['reviewtext'] = review.reviewtext
        if (review.isreplied == 1):
            review_data['responsetext'] = review.responsetext
        else:
            review_data['responsetext'] = ''
        review_data['username']=review.user.name
        review_data['postdate']=review.postdate
        review_data['isreplied']=review.isreplied
        review_data['restaurantid']=public_id
        review_data['reviewid'] = review.reviewid
        reviews_data.append(review_data)

    return jsonify(reviews_data)


@app.route('/getallowners' , methods=['GET'])
@jwt_required

def get_all_owners():
    owners = User.query.filter_by(roleid=2)
    if not owners:
        return jsonify([])
    
    get_all_owners = []
    for owner in owners:
        get_owner={}
        get_owner['publicid'] = owner.publicid
        get_owner['name'] = owner.name    
        get_owner['email'] = owner.email
        get_all_owners.append(get_owner)
    
    return jsonify(get_all_owners)

@app.route('/getallusers' , methods=['GET'])
@jwt_required

def get_all_users():
    userid = get_jwt_identity()
    user = User.query.filter_by(publicid=userid).first()
    if user.roleid != 1 :
        print(user.roleid)
        return jsonify([])
    owners = User.query.filter_by(roleid=3)
    if not owners:
        return jsonify([])
    
    get_all_owners = []
    for owner in owners:
        get_owner={}
        get_owner['publicid'] = owner.publicid
        get_owner['name'] = owner.name    
        get_owner['email'] = owner.email
        get_all_owners.append(get_owner)
    return jsonify(get_all_owners)

@app.route('/deletereview' , methods=['POST'])
@jwt_required

def delete_review():
    data = request.get_json(force = True) 
    review = Review.query.filter_by(reviewid = data['reviewid']).first()

    if not review:
        return jsonify({'message' : 'Review Not Found' })
    
    db.session.delete(review)
    db.session.commit()
    
    return jsonify({'message' : 'Review Deleted Successfully!!!' })


@app.route('/deleterestaurant' , methods=['POST'])
@jwt_required

def delete_restaurant():
    data = request.get_json(force = True) 
    restaurant = Restaurant.query.filter_by(restaurantpublicid = data['restaurantpublicid']).first()

    if not restaurant:
        return jsonify({'message' : 'Restaurant Not Found' })
    
    user = User.query.filter_by(publicid = restaurant.userpublicid).first()
    role = Role.query.filter_by(roleid=3).first()
    user.role = role  
    
    db.session.delete(restaurant)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message' : 'Restaurant Deleted Successfully!!!' })

 



if __name__ == "__main__":
    app.run(debug=True)