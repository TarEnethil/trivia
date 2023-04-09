## Installation

```bash
python3 -m venv trivia_env
. trivia_env/bin/activate
pip install -r requirements.txt
cp config/config.py.template config/config.py
(adjust config/config.py)
```

## Init for local test

```bash
. trivia_env/bin/activate
export FLASK_APP=trivia.py
flask db init
flask db migrate
flask db upgrade
flask run -h localhost
```
Open [trivia page on localhost](http://127.0.0.1:5000/\_\_install\_\_) and create admin account.

## Local test

```bash
. trivia_env/bin/activate
export FLASK_APP=trivia.py
flask run -h localhost
```

## Docker

```bash
docker build . -t trivia:latest
docker-compose up -d
```

## API endpoints

+ /api: redirects to /api/latest
+ /api/latest: latest published trivia
+ /api/\<id\>: trivia by id
+ /api/random: random published trivia

### Fields
* id: publish count of this entry
* fact: actual trivia text
* category: category of the trivia
* sent_by (option): person who sent in the fact (only present if field is set)
