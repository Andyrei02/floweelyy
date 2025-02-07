from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import RegistrationForm

from app.models import db, Flower, Order, User


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
