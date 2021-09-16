import uuid

from sqlalchemy import Column, Integer, Numeric, String
from sqlalchemy.types import DateTime
from sqlalchemy.ext.declarative import declarative_base


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
