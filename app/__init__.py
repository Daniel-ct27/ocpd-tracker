from flask import Flask

from flask_login import LoginManager
from .extension import db
from .models import User, ProgramAdmin,Program, Event, Assignment, AssignmentCompletion,Attendance

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'supersecret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tracker.db'

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"



    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, user_id)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app