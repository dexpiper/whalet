import os

from whalet.factory import create_app
from whalet.check import Abort
from whalet import models
from whalet.database import Database


# creating app
app = create_app()
app.logger.info('App created')

# CHANGE TO FALSE for using real database
app.config['TESTING'] = True

app.logger.info('Creating database...')

# creating database, session and tables
if app.config['TESTING']:
    app.logger.warning('App using SQLight temporary db')
    dbase = Database()
    MASTER_TOKEN = 'whalesome'

else:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URI']
    MASTER_TOKEN = os.environ['MASTER_TOKEN']
    dbase = Database(url=SQLALCHEMY_DATABASE_URI)

db = dbase.create_session()
models.Base.metadata.create_all(bind=dbase.engine)

app.logger.info('Registering aborter helper...')

# creating Abort instance to help with errors
# in user requests
abort = Abort(app, db)

# registering database and abort helper in app
app.config['DATABASE_SESSION'] = db
app.config['ABORT_HELPER'] = abort
app.config['MASTER_TOKEN'] = MASTER_TOKEN

with app.app_context():

    app.logger.info('Registering blueprint...')

    # getting and registering routes from blueprint
    from whalet import routes
    app.register_blueprint(routes.main)

app.logger.info('Done with setting.')

if __name__ == '__main__':
    app.logger.info('Starting app...')
    app.run(host="0.0.0.0", debug=True, threaded=True)
