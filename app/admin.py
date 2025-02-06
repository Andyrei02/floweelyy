import os
from flask import Flask, redirect, url_for, request, render_template
from flask_admin import Admin, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from app.models import db, Flower, Order, AdminUser

UPLOAD_FOLDER = 'app/static/images/catalog'

# Настраиваем авторизацию
login_manager = LoginManager()
login_manager.login_view = "admin.login"

class LoginForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))

# Класс для защиты админки
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin.login"))

# Главная страница админки
class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for("admin.login"))
        return super().index()

    @expose('/login', methods=['GET', 'POST'])
    def login(self):
        form = LoginForm()
        if form.validate_on_submit():
            user = AdminUser.query.filter_by(username=form.username.data).first()
            if user and check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for("admin.index"))
        import os
        print("Текущий каталог:", os.getcwd())  # Проверяем, где запущено приложение
        print("Содержимое templates/admin:", os.listdir("app/templates/admin"))
        return render_template("admin/login.html", form=form)

    @expose('/logout')
    @login_required
    def logout(self):
        logout_user()
        return redirect(url_for("admin.login"))

# Форма для загрузки изображений
class FlowerAdmin(SecureModelView):
    form_extra_fields = {
        'image_url': StringField('URL изображения')
    }

    def on_model_change(self, form, model, is_created):
        file = request.files.get('image')
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            model.image_url = f'images/catalog/{filename}'

def setup_admin(app: Flask):
    admin = Admin(app, name="Админ-панель", template_mode="bootstrap4", index_view=MyAdminIndexView())

    admin.add_view(FlowerAdmin(Flower, db.session, name="Цветы"))
    admin.add_view(SecureModelView(Order, db.session, name="Заказы"))
