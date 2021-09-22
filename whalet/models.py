import uuid

from sqlalchemy import Column, Integer, Numeric, String
from sqlalchemy.types import DateTime
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash


Base = declarative_base()


class Operation(Base):

    __tablename__ = 'Operations'

    id = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    optype = Column(String(20))    # enum?
    time = Column(DateTime)
    amount = Column(Numeric(10, 2))
    sent_to = Column(String(20))
    get_from = Column(String(20))


class Wallet(Base):

    __tablename__ = 'Wallets'

    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    balance = Column((Numeric(10, 2)))
    password_hash = Column(String(128))

    def hash_password(password) -> str:
        '''
        Hashing given password string to store
        '''
        hash = generate_password_hash(password)
        return hash

    def verify_password(session, name, password) -> bool:
        '''
        Varifying given password for given wallet name.
        Argument session (<db> var in whalet.routes)
        needed.
        '''
        wallet = session.query(Wallet).filter(
            Wallet.name == name).first()
        result = check_password_hash(
            pwhash=wallet.password_hash,
            password=password
        )
        return result
