from main import app, db
from app.models import AdminUser
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = AdminUser(username="admin", password=generate_password_hash("secret"))
    db.session.add(admin)
    db.session.commit()


with app.app_context():
    db.create_all()
