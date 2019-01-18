import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))
SQLITE_DB = 'sqlite:///' + os.path.join(BASEDIR, 'instance', 'data.db')


class Config(object):

    SECRET_KEY = 'COMIC'
    SQLALCHEMY_DATABASE_URI = SQLITE_DB
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    DEBUG = False

    BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERY_SEND_TASK_SENT_EVENT = True


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    pass


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}