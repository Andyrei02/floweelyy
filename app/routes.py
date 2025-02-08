import json

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import RegistrationForm

from app.models import db, Flower, Order, User, Cart


main_bp = Blueprint('main', __name__)
auth_bp = Blueprint("auth", __name__)

# Настраиваем авторизацию
login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        return user
    return AdminUser.query.get(int(user_id))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect (url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(
            name=form.name.data, 
            email=form.email.data, 
            phone=form.phone.data, 
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Регистрация успешна! Теперь вы можете войти в систему.", "success")
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect (url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash("Неверный email или пароль.", "danger")
    return render_template("auth/login.html")


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    if user:
        db.session.delete(user)
        db.session.commit()
        logout_user()
        flash("Ваш аккаунт был удалён.", "success")
    else:
        flash("Ошибка при удалении аккаунта.", "danger")

    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    
    
    return render_template("auth/profile.html", user=current_user, orders=orders)


@main_bp.route('/cart')
def cart():
    if current_user.is_authenticated:
        cart_items = db.session.query(Cart, Flower).join(Flower).filter(Cart.user_id == current_user.id).all()
        cart_data = [{'flower': flower, 'quantity': cart.quantity} for cart, flower in cart_items]
    else:
        cart_data = []
        if 'cart' in session:
            flower_ids = [item['flower_id'] for item in session['cart']]
            flowers = Flower.query.filter(Flower.id.in_(flower_ids)).all()
            flower_dict = {flower.id: flower for flower in flowers}
            
            for item in session['cart']:
                flower = flower_dict.get(item['flower_id'])
                if flower:
                    cart_data.append({'flower': flower, 'quantity': item['quantity']})
    
    return render_template('cart.html', cart=cart_data)


@main_bp.route('/add_to_cart/<int:flower_id>', methods=['POST'])
def add_to_cart(flower_id):
    if current_user.is_authenticated:
        # Если пользователь авторизован, добавляем в БД
        existing_item = Cart.query.filter_by(user_id=current_user.id, flower_id=flower_id).first()
        if existing_item:
            existing_item.quantity += 1  # Увеличиваем количество
        else:
            new_cart_item = Cart(user_id=current_user.id, flower_id=flower_id, quantity=1)
            db.session.add(new_cart_item)
        db.session.commit()
    else:
        # Если пользователь не авторизован, храним в session
        if 'cart' not in session:
            session['cart'] = []
        cart = session['cart']
        
        for item in cart:
            if item['flower_id'] == flower_id:
                item['quantity'] += 1
                break
        else:
            cart.append({'flower_id': flower_id, 'quantity': 1})
        
        session.modified = True  # Обновляем сессию

    return redirect(url_for('main.cart'))


@main_bp.route('/remove_from_cart/<int:flower_id>', methods=['POST'])
def remove_from_cart(flower_id):
    if current_user.is_authenticated:
        cart_item = Cart.query.filter_by(user_id=current_user.id, flower_id=flower_id).first()
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()
    else:
        if 'cart' in session:
            session['cart'] = [item for item in session['cart'] if item['flower_id'] != flower_id]
            session.modified = True

    return redirect(url_for('main.cart'))


@main_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'GET':
        if current_user.is_authenticated:
            user_name = current_user.name
            user_phone = current_user.phone
            return render_template("checkout.html", name=user_name, phone=user_phone)
        
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')

        if not name or not phone or not address:
            flash("Заполните все поля!", "danger")
            return redirect(url_for('main.checkout'))

        # Получаем корзину
        cart_data = []
        if current_user.is_authenticated:
            cart_items = db.session.query(Cart, Flower).join(Flower).filter(Cart.user_id == current_user.id).all()
            cart_data = [{'flower': flower, 'quantity': cart.quantity} for cart, flower in cart_items]
        else:
            if 'cart' in session:
                flower_ids = [item['flower_id'] for item in session['cart']]
                flowers = Flower.query.filter(Flower.id.in_(flower_ids)).all()
                flower_dict = {flower.id: flower for flower in flowers}

                for item in session['cart']:
                    flower = flower_dict.get(item['flower_id'])
                    if flower:
                        cart_data.append({'flower': flower, 'quantity': item['quantity']})

        if not cart_data:
            flash("Ваша корзина пуста!", "danger")
            return redirect(url_for('main.cart'))

        # Создаём JSON с товарами
        items_json = json.dumps([
            {'name': item['flower'].name, 'quantity': item['quantity'], 'price': item['flower'].price}
            for item in cart_data
        ])

        total_price = sum(item['flower'].price * item['quantity'] for item in cart_data)

        new_order = Order(
            user_id=current_user.id if current_user.is_authenticated else None,
            customer_name=name,
            customer_phone=phone,
            customer_address=address,
            items=items_json,
            total_price=total_price
        )
        db.session.add(new_order)
        db.session.commit()

        # Очищаем корзину
        if current_user.is_authenticated:
            Cart.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()
        else:
            session.pop('cart', None)

        flash("Заказ успешно оформлен!", "success")
        return redirect(url_for('main.index'))

    return render_template("checkout.html")


@main_bp.route('/')
def index():
    flowers = Flower.query.all()
    return render_template('index.html', flowers=flowers)


@main_bp.route('/catalog')
def catalog():
    flowers = Flower.query.all()
    return render_template('catalog.html', flowers=flowers)


@main_bp.route('/flower/<string:flower_name>')
def flower_detail(flower_name):
    flower = Flower.query.filter_by(name=flower_name).first()
    if not flower:
        flash("Такой букет не найден.", "danger")
        return redirect(url_for('main.catalog'))
    
    return render_template('flower_detail.html', flower=flower)


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

