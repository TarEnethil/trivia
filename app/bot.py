import re
import telebot
from flask import current_app, render_template, redirect, flash, request, jsonify, url_for
from flask_login import login_required
from datetime import datetime
import time

rgx = re.compile("/trivia (\d+)")

def log_message(message):
    if current_app.config["TELEGRAM_BOT_LOG"] == None or current_app.config["TELEGRAM_BOT_LOG"] == False:
        return

    if message.from_user.username:
        user = message.from_user.username
    else:
        user = message.from_user.first_name

    print("{}: {} sent message '{}'".format(datetime.fromtimestamp(message.date), user, message.text))

def setup_bot(app, bp, bot):
    from app.helpers import page_title, redirect_non_admins, get_published_count, get_published_count_cat, publish_trivia, get_random_ready, send_to_owner, send_to_channel, get_ready_count, get_bot_token, gen_new_bot_token, get_random_published_id, get_published

    @bp.route("/bot/", methods=["GET"])
    @login_required
    def bot_index():
        redirect_non_admins()

        if bot != None and current_app.config["TELEGRAM_WEBHOOK_HOST"] != None:
            configured = True

            status = bot.get_webhook_info()

            if not status.url or status.url == '':
                webhook_active = False
                webhook_url = None
                webhook_warning = False
            elif status.url != "{}/bot/update/{}/".format(current_app.config["TELEGRAM_WEBHOOK_HOST"], current_app.config["TELEGRAM_TOKEN"]):
                webhook_active = True
                webhook_warning = True
                webhook_url = status.url
            else:
                webhook_active = True
                webhook_warning = False
                webhook_url = status.url

            return render_template("trivia/bot.html", configured=configured, webhook_active=webhook_active, webhook_warning=webhook_warning, webhook_url=webhook_url, title=page_title("Bot Status"))
        else:
            return render_template("trivia/bot.html", configured=False, title=page_title("Bot Status"))

    @bp.route("/bot/webhook/activate", methods=["GET"])
    @login_required
    def bot_webhook_activate():
        if app.config["TELEGRAM_WEBHOOK_HOST"] != None and bot != None:
            wurl = "{}/bot/update/{}/".format(current_app.config["TELEGRAM_WEBHOOK_HOST"], current_app.config["TELEGRAM_TOKEN"])

            webhook = bot.get_webhook_info()

            if not webhook.url or webhook.url == '' or webhook.url != wurl:
                try:
                    print("trying to register webhook url {}".format(wurl))
                    bot.remove_webhook()
                    time.sleep(0.2)
                    bot.set_webhook(url=wurl)
                except Exception as ex:
                    flash("something went wrong while disabling + enabling the webhook: " + ex, "danger")
                    return redirect(url_for("trivia.bot_index"))

                flash("webhook was enabled", "success")
            else:
                flash("webhook was still active and correct, did not take action", "warning")
        else:
            flash("not all configs for bots are enabled...", "danger")

        return redirect(url_for("trivia.bot_index"))

    @bp.route("/bot/webhook/deactivate", methods=["GET"])
    @login_required
    def bot_webhook_deactivate():
        if current_app.config["TELEGRAM_WEBHOOK_HOST"] != None and bot != None:
            try:
                bot.remove_webhook()
            except:
                flash("something went wrong while disabling the webhook", "danger")
                return redirect(url_for("trivia.bot_index"))

                flash("webhook was disabled", "success")
        else:
            flash("not all configs for bots are enabled...", "danger")

        return redirect(url_for("trivia.bot_index"))

    @bp.route("/bot/publish", methods=["GET"])
    def bot_publish():
        if bot != None:
            url_token = request.args.get('token')
            our_token = get_bot_token()

            if url_token == None or url_token != our_token:
                return jsonify({"success": False}), 403

            t = get_random_ready()

            if t == None:
                send_to_owner(bot, "I was triggered to send a trivia, but there was none left!")
                return jsonify({"success": False}), 503

            from app import db
            publish_trivia(db, t.id)

            send_to_channel(bot, t.description + "\n\nSent by @ThorstensTriviaBot")

            msg_to_owner = ""

            if current_app.config["TELEGRAM_ALWAYS_REPORT"]:
                msg_to_owner = "I just posted the Trivia '{}' to the channel.\n".format(t.title)

            ready = get_ready_count(db)

            warn = current_app.config["TELEGRAM_WARN_COUNT"]
            if warn and ready < warn:
                msg_to_owner += "Warning: "

            if current_app.config["TELEGRAM_ALWAYS_REPORT"] or (warn and ready < warn):
                msg_to_owner += "There are {} trivia left in the 'ready' lane.".format(ready)

            if msg_to_owner != "":
                send_to_owner(bot, msg_to_owner)

            gen_new_bot_token()
            return jsonify({"success": True}), 200

    @bp.route("/bot/update/{}/".format(app.config["TELEGRAM_TOKEN"]), methods=["POST"])
    def webhook():
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return 'ok', 200
        else:
            flask.abort(403)

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
        msg += "If you find any bugs, feel free to report them to @TriviaThorsten or at https://github.com/tarenethil/trivia/issues"

        if current_app.config["TELEGRAM_BOT_LOG"] == True:
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

        t = get_published(tid)

        if t == None:
            bot.reply_to(message, "Sorry, I could not find the fact with id {}.".format(tid))
            return

        bot.send_message(message.chat.id, t.description)

    def admin_add_message(message):
        print(message)
        return message.chat.id == app.config["TELEGRAM_OWNER_CHAT_ID"]

    @bot.message_handler(func=admin_add_message)
    def admin_add(message):
        from app import db
        from app.helpers import add_new_trivia

        trivia_text = None
        if message.text.startswith("/add "):
            trivia_text = message.text[len("/add "):]
        elif "http" in message.text:
            trivia_text = message.text

        if trivia_text != None:
            add_new_trivia(db, "Added via Telegram", trivia_text)
            bot.reply_to(message, "Trivia added")

    @bot.message_handler(func=lambda m: True)
    def default(message):
        log_message(message)