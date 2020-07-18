#!venv/bin/python

from app import app, db, bot
from app.models import Trivia
from app.helpers import get_published, get_random_published_id, get_published_count
from datetime import datetime
import re

import telebot

rgx = re.compile("/trivia (\d+)")

if bot == None:
    print("no token configured")
    exit(1)

def log_message(message):
    if app.config["TELEGRAM_BOT_LOG"] == None or app.config["TELEGRAM_BOT_LOG"] == False:
        return

    if message.from_user.username:
        user = message.from_user.username
    else:
        user = message.from_user.first_name

    print("{}: {} sent message '{}'".format(datetime.fromtimestamp(message.date), user, message.text))

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    log_message(message)
    msg = "Hello @{}!\n\n".format(message.from_user.username)
    msg += "I am @ThorstensTriviaBot (WIP). I currently support the following commands:\n\n"
    msg += "/random, /trivia\n"
    msg += "        get a random published fact\n"
    msg += "/trivia <number>\n"
    msg += "        get published trivia #<number>"
    msg += "\n\nThere are currently {} published facts.\n".format(get_published_count())
    msg += "If you find any bugs, feel free to report them to @TriviaThorsten or at https://tarenethil.github.com/trivia/issues"

    if app.config["TELEGRAM_BOT_LOG"] == True:
        msg += "\n\nNote: For debugging purposes, all messages are currently logged."

    bot.send_message(message.chat.id, msg)

@bot.message_handler(commands=['random'])
def random_trivia(message):
    log_message(message)
    t = get_published(get_random_published_id())

    bot.send_message(message.chat.id, t.description)

@bot.message_handler(commands=['trivia'])
def trivia(message):
    log_message(message)
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

@bot.message_handler(func=lambda m: True)
def default(message):
    log_message(message)

bot.polling()
