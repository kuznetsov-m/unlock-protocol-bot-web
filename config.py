import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # DEBUG = False
    DEBUG = True
    SECRET_KEY = os.environ['FLASK_APP_SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False