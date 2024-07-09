from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
api = Api(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=True, nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.String(120), unique=True, nullable=False)
    quantity = db.Column(db.String(120), unique=True, nullable=False)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, nullable=False)


class ProductList(Resource):
    def get(self):
        products = Product.query.all()
        result = []
        for product in products:
            result.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': product.quantity
            })
        return jsonify({
            'data' : result,
            'status' : 'success'
        })


def create_database():
    with app.app_context():
        db.create_all()
    print('Database created')        


class Register(Resource):
    def post(self):
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'})
        try:
            user = User(username=data['username'], password=generate_password_hash(data['password']))
            db.session.add(user)
            db.session.commit()
            return jsonify({'message': 'User registered successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'An error occurred'})


class Login(Resource):
    def post(self):
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        try:
            user = User.query.filter_by(username=data['username']).first()
            if user and check_password_hash(user.password, data['password']):
                return {'message': 'Login successful', 'user_id': user.id}, 200
            else:
                return jsonify({'message': 'Invalid username or password'}), 401
        except Exception as e:
            return jsonify({'message': 'An error occurred', error: str(e)}), 500


class AddProduct(Resource):
    def post(self):
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'})
        try:
            product = Product(name=data['name'], price=data['price'], quantity=data['quantity'])
            db.session.add(product)
            db.session.commit()
            return jsonify({'message': 'Product added successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'An error occurred'})


class UserList(Resource):
    def get(self):
        try:
            users = User.query.all()
            return jsonify([
                {'id': user.id, 'username': user.username} for user in users
            ])
        except Exception as e:
            return jsonify({'message': 'An error occurred'})


class UpdateCart(Resource):
    def put(self, product_id):
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'})
        try:
            product = CartItem.query.filter_by(product_id=product_id).first()
            if not product:
                return jsonify({'message': 'Product not found in cart'})

            product.quantity = data['quantity']
            db.session.commit()
            return jsonify({'message': 'Cart item updated successfully'})

        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'An error occurred'})

class CartList(Resource):
    def get(self, user_id):            
        try:
            cart_items = CartItem.query.filter_by(user_id=user_id).all()
            return jsonify([
                {'id': cart_item.id, 'product_id': cart_item.product_id, 'quantity': cart_item.quantity} for cart_item in cart_items
            ])
        except Exception as e:
            return jsonify({'message': 'An error occurred'})


class AddToCart(Resource):
    def post(self):
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'})
        try:
            cart_item = CartItem(user_id=data['user_id'], product_id=data['product_id'], quantity=data['quantity'])
            db.session.add(cart_item)
            db.session.commit()
            return jsonify({'message': 'Product added to cart successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'An error occurred'})        

class remove_from_cart(Resource):
    def delete(self, user_id):              
        try:
            cart_item = CartItem.query.filter_by(user_id=user_id).first()
            if not cart_item:
                return jsonify({'message': 'Cart item not found'})
            db.session.delete(cart_item)
            db.session.commit()
            return jsonify({'message': 'Cart item deleted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'An error occurred'})


api.add_resource(ProductList, '/products')
api.add_resource(AddProduct, '/add_product')
api.add_resource(AddToCart, '/add_to_cart')
api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
api.add_resource(UserList, '/users')
api.add_resource(UpdateCart, '/update_cart/<int:product_id>')
api.add_resource(CartList, '/cart_list/<int:user_id>')
api.add_resource(remove_from_cart, '/remove_from_cart/<int:user_id>')

if __name__ == '__main__':
    create_database()
    app.run(debug=True, port=5001)