from flask import Flask
from config.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from app.bot import setup_bot
import telebot


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
bootstrap = Bootstrap()
bot = None

def create_app(config=Config):
    app = Flask(__name__)

    app.config.from_object(config)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    login.login_view = 'main.login'
    bootstrap.init_app(app)

    if app.config["TELEGRAM_TOKEN"] != None:
        bot = telebot.TeleBot(app.config["TELEGRAM_TOKEN"], threaded=False)
        app.config["BOT"] = bot

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix="/user")

    from app.trivia import bp as trivia_bp
    if bot is not None:
        setup_bot(app, trivia_bp, bot)
    app.register_blueprint(trivia_bp)


    return app

from app import models