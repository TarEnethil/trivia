#!venv/bin/python

from app import app, db
from app.models import Trivia
from app.helpers import get_published, get_random_published_id, get_published_count
from uuid import uuid4
import re

import telebot

rgx = re.compile("/trivia (\d+)")

if app.config["TELEGRAM_TOKEN"] == None:
    print("no token configured")
    exit(1)

bot = telebot.TeleBot(app.config["TELEGRAM_TOKEN"])

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = "Hello @{}!\n\n".format(message.from_user.username)
    msg += "I am @ThorstensTriviaBot (WIP). I currently support the following commands:\n\n"
    msg += "/random, /trivia\n"
    msg += "        get a random published fact\n"
    msg += "/trivia <number>\n"
    msg += "        get published trivia #<number>"
    msg += "\n\nThere are currently {} published facts.\n".format(get_published_count())
    msg += "If you find any bugs, feel free to report them to @TriviaThorsten or at https://tarenethil.github.com/trivia/issues"

    bot.send_message(message.chat.id, msg)

@bot.message_handler(commands=['random'])
def random_trivia(message):
    t = get_published(get_random_published_id())

    bot.send_message(message.chat.id, t.description)

@bot.message_handler(commands=['trivia'])
def trivia(message):
    if message.text == "/trivia":
        random_trivia(message)
        return

    m = rgx.match(message.text)

    if m == None:
        bot.reply_to(message, "I could not extract a valid fact id from your query.")
        return

    try:
        tid = int(m.group(1))
    except:
        bot.reply_to(message, "I could not extract valid fact id from your query (target was {}).".format(m.group(1)))
        return

    if tid <= 0:
        bot.reply_to(message, "{} is not a valid fact id.".format(tid))
        return

    t = Trivia.query.filter(Trivia.lane==3).order_by(Trivia.lane_switch_ts.asc()).offset(tid-1).first()

    if t == None:
        bot.reply_to(message, "Sorry, I could not find the fact with id {}.".format(tid))
        return

    bot.send_message(message.chat.id, t.description)

bot.polling()
