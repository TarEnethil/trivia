## Installation

```bash
virtualenv trivia_env
. trivia_env/bin/activate
pip install -r requirements.txt
```

## Init for local test

```bash
. trivia_env/bin/activate
export FLASK_APP=thorstenstrivia.py
flask db init
flask db migrate
flask db upgrade
flask run -h localhost
```
Open (trivia page on localhost)[http://127.0.0.1:5000/\_\_install\_\_] and create admin account.

## Local test

```bash
. trivia_env/bin/activate
export FLASK_APP=thorstenstrivia.py
flask run -h localhost
```

## API endpoints

 * /api: redirects to /api/latest
 * /api/latest: latest published trivia
 * /api/\<id\>: trivia by id
