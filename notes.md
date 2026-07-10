# What I am doing?

## Project Scaffold

- clone the project with fine-grain-token
- scaffold backend with uv.
- scaffold frontend with pnpm -> `pnpm create vue`
- add axios.
- add start.sh

## Project Config

It was hectic but I learned a few things here, let list them out extension wise. But before that, there is a basic separation I have tried to follow in the `backend` as much as possible. The `backend` is divided into 3 main parts:

- Pull the extension from `extensions.py`.
- Add the configuration in `config.py`.
- Initialize the extension in `__init__.py`.
- Then use the extension in the `routes.py` or `models.py` or wherever needed.
- Finally, the `app` is created in `__init__.py` and then run in `app.py`.

### Caching/Redis

It wasn't that hard to implement caching with `Flask-Caching` and `Redis`. The only thing which is to be noted is I have changed redis configuration in `config.py`. There were few *config keys* which were quite new to me, but *chatgpt* helped me a lot in understanding them. I have also added a new function `get_redis_client` to get the redis client with the given db number.

### Celery

By far the most complex one, since I want to use a minimal structure of (`config`, `extensions`, `__init__`) I was simply not following the standard way of creating a celery instance. Here I did something contrary to the standard way, I created a celery instance in `extensions.py` and then initialized it in `__init__.py`. And one other **non-standard practice** *I  injected one extra attribute `extended_config` to the app instance* which is a copy of the `config` class. This was done so that I can access the configuration variables in the celery instance, without rejecting them just because they are not in UPPERCASE, this is what *app.config.from_object* does. Just to bypass this restriction, I created a copy of the config class and then injected it to the app instance. This way I can access all the configuration variables in the celery instance.

Now further Celery setup can be broken down into 2 parts:

#### Task Setup/ Worker Setup

Not that hard just I have learn the basics of celery and how to create a task and how to run a worker. I then created a simple task to add two numbers and then run the worker to see if it works or not. It worked like a charm after a few trials and errors.

#### Task Scheduling

A bit overwhelming at first, but then I learned the basics of celery beat and how to schedule a task. I then created a simple task to print just hello world and then schedule it to run every 10 seconds. Yes that also worked after few tries.

>One Important thing I learned here, is about the celery command in cli how it interpretes the arguments, I was passing the `-A` argument with the `app` instance but it was not working, then I realized that it should be the `celery` instance which is created in `extensions.py`. Then I imported the `celery` instance in `app.py` and then passed it to the cli command, and it worked as expected.

### Mail

It wasn't that hard to implement mail with `Flask-Mail`. I just took the `app-password` from my gmail account and then used it in the `config.py` to send mail. I then created a simple route to send mail and then tested it with browser. Worked in first try.

### SQLALCHEMY

The most simplest so far.

```
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
db.init_app(app)
```

The only thing which is to be noted is I have changed sqlite configuration in `extensions.py` so it can respect *foreign keys* constraints and have *write ahead logging* enabled.

### Session/CORS

The first goal I set in my application is make the CORS work properly, so that I can make the frontend and backend communicate with each other. I then learned about `Flask-CORS` and `Flask-Session` and how to use them. I then created a simple route to test the session and CORS. It worked like a charm after a few trials and errors. Not hard to implement, just a few lines of code in `config.py` and `extensions.py` and then initialize them in `__init__.py`.

### Password Hashing

I used the best available library for password hashing `argon2-cffi` which is a wrapper around the `argon2` library. It is the best available library for password hashing. Just two simple functions in `extensions.py` to hash and verify passwords with *exception handling*.

