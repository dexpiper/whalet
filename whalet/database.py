'''
Defining database
'''
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Database:
    '''
    Create engine on initialization and
    create session.
    '''

    def __init__(
            self,
            url='sqlite:///./whalet.db'
    ):

        self.url = url
        self.engine = self.make_engine()

    def make_engine(self):
        engine = create_engine(
            self.url,
            connect_args={'check_same_thread': False}
        )
        return engine

    def create_session(self):
        SessionLocal = sessionmaker(bind=self.engine)
        return SessionLocal()
