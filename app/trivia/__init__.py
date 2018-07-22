from flask import Blueprint

bp = Blueprint("trivia", __name__)

from app.trivia import routes