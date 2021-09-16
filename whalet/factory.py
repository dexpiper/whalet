'''
Creating Flask instance and initiating database
'''
from logging.config import dictConfig

from flask import Flask

from whalet.config.loggingconf import flask_log_conf


def create_app():
    '''
    Creating Flask application
    '''
    # setting logging using flask.app.logger
    dictConfig(flask_log_conf)

    # setting Flask
    app = Flask(__name__)

    return app
