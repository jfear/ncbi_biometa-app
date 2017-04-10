class Config(object):
    SECRET_KEY = 'XMLZODSHE8N6NFOZDPZA2HULWSIYJU45K6N4ZO9M'
    MONGODB_HOST = '128.231.83.74'
    MONGODB_PORT = 27022


class ProdConfig(Config):
    MONGODB_DB = 'sra2'
    DEBUG = False


class DevConfig(Config):
    MONGODB_DB = 'test'
    DEBUG = True
