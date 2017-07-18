import os

class Config(object):
    MONGODB_DB = 'sra2'


class ProdConfig(Config):
    SECRET_KEY = os.environ['SECRET_KEY']
    MONGODB_HOST = os.environ['DB_HOST']
    MONGODB_PORT = os.environ['DB_PORT']
    MONGODB_USERNAME = os.environ['DB_USERNAME']
    MONGODB_PASSWORD = os.environ['DB_PASSWORD']
    DEBUG = False


class DevConfig(Config):
    SECRET_KEY = 'XMLZODSHE8N6NFOZDPZA2HULWSIYJU45K6N4ZO9M'
    MONGODB_HOST = 'mongo.genetics.underground.com'
    MONGO_PORT = 27022
    MONGO_USERNAME = 'sra'
    MONGO_PASSWORD = 'oliver'
    DEBUG = True
