import os

class Config(object):
    MONGODB_DB = 'sra'


class ProdConfig(Config):
    SECRET_KEY = os.getenv('SECRET_KEY')
    MONGODB_HOST = os.getenv('DB_HOST')
    MONGODB_PORT = os.getenv('DB_PORT')
    MONGODB_USERNAME = os.getenv('DB_USERNAME')
    MONGODB_PASSWORD = os.getenv('DB_PASSWORD')
    DEBUG = False


class DevConfig(Config):
    SECRET_KEY = 'XMLZODSHE8N6NFOZDPZA2HULWSIYJU45K6N4ZO9M'
    MONGODB_HOST = '127.0.0.1'
    MONGO_PORT = 27017
    DEBUG = True
