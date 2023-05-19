#!/bin/bash

URL="localhost:8337"
DIR=$(dirname $0)
TOKEN=$(sqlite3 $DIR/data/app.db "SELECT bot_token FROM general_settings WHERE id = 1")

curl $URL/bot/publish?token=$TOKEN
