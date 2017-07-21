import os

class Config(object):
    MONGODB_DB = os.getenv('MONGODB_DB')
    SECRET_KEY = os.getenv('SECRET_KEY')
    MONGODB_HOST = os.getenv('MONGODB_HOST')
    MONGODB_PORT = int(os.getenv('MONGODB_PORT'))


class ProdConfig(Config):
    DEBUG = False


class DevConfig(Config):
    DEBUG = True
