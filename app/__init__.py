import os
from celery import Celery
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config, Config


db = SQLAlchemy()
celery = Celery(__name__, broker=Config.BROKER_URL)


def create_app():

    app = Flask(__name__, instance_relative_config=True)

    if not os.path.exists(app.instance_path):
        os.mkdir(app.instance_path)

    app.config.from_object(config['development'])
    celery.config_from_object(app.config)

    db.init_app(app)

    from app import models
    app.cli.add_command(models.init_db_command)
    from app import comic
    app.register_blueprint(comic.bp)
    from app import auth
    app.register_blueprint(auth.bp)
    return app
