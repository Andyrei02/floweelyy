from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate

from app.models import db
from app.routes import main_bp, auth_bp, login_manager
from app.admin import setup_admin
from config import Config


app = Flask(__name__, static_folder="app/static", template_folder="app/templates")
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

login_manager.login_view = "auth.login"  # Указываем, что для пользователей логин здесь
login_manager.init_app(app)

setup_admin(app)

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp, url_prefix="/auth")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
