import configparser

config = configparser.ConfigParser()

config.read('config.ini')

KAGGLE_USERNAME = config['DEFAULT']['KAGGLE_USERNAME']
KAGGLE_KEY = config['DEFAULT']['KAGGLE_KEY']