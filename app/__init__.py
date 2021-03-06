from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)

from app.user import bp as user_bp
app.register_blueprint(user_bp, url_prefix="/user")

from app.trivia import bp as trivia_bp
app.register_blueprint(trivia_bp)

from app import routes, models