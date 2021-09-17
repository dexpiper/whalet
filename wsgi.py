#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from whalet.factory import create_app
from whalet.check import Abort
from whalet import models
from whalet.database import Database


# creating app
app = create_app()

# settings
SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']


if __name__ == '__main__':

    # creating database, session and tables
    dbase = Database(url=SQLALCHEMY_DATABASE_URI)
    db = dbase.create_session()
    models.Base.metadata.create_all(bind=dbase.engine)

    # creating Abort instance to help with errors
    # in user requests
    abort = Abort(app, db)

    # registering database and abort helper in app
    app.config['DATABASE_SESSION'] = db
    app.config['ABORT_HELPER'] = abort

    with app.app_context():
        # getting and registering routes from blueprint
        from whalet import routes
        app.register_blueprint(routes.main)

    app.run(debug=True)
