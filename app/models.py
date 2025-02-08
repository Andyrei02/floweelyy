from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin


db = SQLAlchemy()

class Flower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<Flower {self.name}>'


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Связь с User
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    items = db.Column(db.Text, nullable=False)  # JSON с товарами
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='в ожидании')

    def __repr__(self):
        return f'<Order {self.id} - {self.customer_name}>'


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    flower_id = db.Column(db.Integer, db.ForeignKey('flower.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=False, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    order = db.relationship('Order', backref='user', lazy=True)
    cart_items = db.relationship('Cart', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.name}>'


class AdminUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)  # Хранить хэш пароля!

    def __repr__(self):
        return f'<Admin {self.username}>'