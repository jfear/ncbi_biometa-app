import os

class Config(object):
    MONGODB_DB = 'sra'


class ProdConfig(Config):
    SECRET_KEY = os.getenv('SECRET_KEY')
    MONGODB_HOST = os.getenv('MONGODB_HOST')
    MONGODB_PORT = int(os.getenv('MONGODB_PORT'))
    DEBUG = False


class DevConfig(Config):
    SECRET_KEY = 'XMLZODSHE8N6NFOZDPZA2HULWSIYJU45K6N4ZO9M'
    MONGODB_HOST = 'localhost'
    MONGO_PORT = 27017
    DEBUG = True
