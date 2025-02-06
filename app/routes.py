from flask import Blueprint, render_template, request, redirect, url_for
from app.models import db, Flower, Order

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    flowers = Flower.query.all()
    return render_template('index.html', flowers=flowers)

@main_bp.route('/catalog')
def catalog():
    flowers = Flower.query.all()
    return render_template('catalog.html', flowers=flowers)

@main_bp.route('/order', methods=['POST'])
def place_order():
    name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    items = request.form.get('items')  # JSON-список товаров
    total_price = request.form.get('total_price')

    order = Order(customer_name=name, customer_phone=phone, customer_address=address, 
                  items=items, total_price=total_price)
    db.session.add(order)
    db.session.commit()

    return redirect(url_for('main.index'))
