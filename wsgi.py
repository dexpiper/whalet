import os

from werkzeug.middleware.proxy_fix import ProxyFix

from whalet.factory import create_app
from whalet.check import Abort
from whalet import models
from whalet.database import Database


# creating app
app = create_app()
app.logger.info('App created')

# settings
SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URI']

app.logger.info('Creating database...')

# creating database, session and tables
dbase = Database()  # url=SQLALCHEMY_DATABASE_URI
db = dbase.create_session()
models.Base.metadata.create_all(bind=dbase.engine)

app.logger.info('Registering aborter helper...')

# creating Abort instance to help with errors
# in user requests
abort = Abort(app, db)

# registering database and abort helper in app
app.config['DATABASE_SESSION'] = db
app.config['ABORT_HELPER'] = abort

with app.app_context():

    app.logger.info('Registering blueprint...')

    # getting and registering routes from blueprint
    from whalet import routes
    app.register_blueprint(routes.main)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.logger.info('Starting app...')
app.run(debug=True)
