# Python Standard Library
from datetime import datetime
from decimal import Decimal
from logging.config import dictConfig
import os

# Flask, marhmallow, SQLAlchemy
from flask import Flask, request
from flask import abort as flask_abort
from marshmallow import Schema, fields, ValidationError
from marshmallow import post_load, pre_dump
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

# internal modules
from whalet.check import Abort
from whalet.helpers import cook_response, safe_round
from whalet.config.loggingconf import flask_log_conf
# // under construction
# // from whalet.registry import IdStorage, make_register, get_id


###### SETTING ######

# setting logging using flask.app.logger
dictConfig(flask_log_conf)

# setting Flask
app = Flask(__name__)

#
# CHANGE TO "FALSE" BEFORE DEPLOY
#
TESTMODE = True

if TESTMODE == False:
    MASTER_TOKEN = os.environ['WHALET_TOKEN']
else:
    # master token for testing purposes
    from whalet.config.token import MASTER_TOKEN
    app.logger.warning('Server run in TESTMODE')

# configuring SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///whalets.db"
db = SQLAlchemy(app)

# // creating storage for verifying operations
# // currently under developent
# // idstorage = IdStorage()

# creating Abort class instance for aborting bad requests
abort = Abort(app, db)


###### MODELS ######

class Operations(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # change to uuid4
    optype = db.Column(db.String(20))             # enum?
    time = db.Column(db.DateTime)
    amount = db.Column(db.Numeric(10, 2))
    sent_to = db.Column(db.String(20))
    get_from = db.Column(db.String(20))

class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    balance = db.Column((db.Numeric(10, 2)))


###### SCHEMAS ######

# Custom validators
def must_not_be_blank(data):
    if not data:
        raise ValidationError("Data not provided.")

def must_be_enum(data):
    optypes = ['creation', 'deposit', 'transaction']
    if data not in optypes:
        raise ValidationError("Unsupported operation type")

# Schemas
class OperationSchema(Schema):
    id = fields.Int(dump_only=True)
    optype = fields.Str(validate=must_be_enum)
    time = fields.DateTime()
    amount = fields.Decimal(as_string=True)
    sent_to = fields.Str()
    get_from = fields.Str()

    @post_load
    def make_op(self, data, **kwargs):
        return Operations(**data)
    
class WalletSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    balance = fields.Decimal(as_string=True)

    @post_load
    def make_wallet(self, data, **kwargs):
        return Wallet(**data)

### setting schemas

operation_schema = OperationSchema()
operations_schema = OperationSchema(many=True)
wallet_schema = WalletSchema()
wallets_schema = WalletSchema(many=True)


###### API ######

#
# Get wallet list
#
@app.route('/v1/wallets', methods=['GET'])
def get_wallets():
    '''
    Get all the wallets and their balances
    '''
    abort.if_value_not_specified(arg='token', request=request)
    given_token = request.args['token']
    abort.if_token_incorrect(given_token, MASTER_TOKEN)

    wallets = Wallet.query.all()
    result = wallets_schema.dump(wallets)

    resp = cook_response(app, {'wallets': result})

    return resp, 200

#
# create a wallet
#
@app.route('/v1/create/<wallet_name>', methods=['POST'])
def create_wallet(wallet_name):
    '''
    Creating a new wallet with 0 balance
    '''
    abort.if_wallet_already_exists(
        wallet_name=wallet_name,
        model=Wallet
        )
    try:
        wallet = wallet_schema.load(
            dict(name=wallet_name, balance=Decimal('0')
            ))
    except Exception as exc:
        app.logger.info(f'{exc}')
        flask_abort(500, f'Error during wallet creation')

    operation = operation_schema.load(
        dict(
            optype='creation', 
            time=datetime.now().isoformat(),
            sent_to=wallet_name
            )
        )

    db.session.add(wallet)
    db.session.add(operation)
    db.session.commit()

    resp = cook_response(
        app,
        {f'{wallet_name}:created':'true'}
        )
    
    return resp, 201

#
# get balance for a wallet
#
@app.route('/v1/<wallet_name>/balance', methods=['GET'])
def get_balance(wallet_name):
    '''
    Get balance for given wallet
    '''
    balance = Wallet.query.filter(Wallet.name == wallet_name).first()
    balance = Decimal(str(balance.balance))
    resp = cook_response(
        app,
        {f'{wallet_name}:balance':balance})
    return resp, 200

#
# get op history for a wallet
#
@app.route('/v1/<wallet_name>/history', methods=['GET'])
def get_history(wallet_name):
    '''
    Get history for given wallet
    '''
    operations = Operations.query.filter(
        or_(
            Operations.sent_to == wallet_name,
            Operations.get_from == wallet_name
            )).all()
    result = operations_schema.dump(operations)

    # changing amount sign to "-" 
    # in outcoming transactions

    for el in result:
        if (
            el['get_from'] == wallet_name
        ) and (
            el['optype'] == 'transaction'
        ):
            el['amount'] = '-' + el['amount']

    resp = cook_response(app, {f'{wallet_name}:operations': result})

    return resp, 200

#
# deposit money to wallet
#
@app.route('/v1/<wallet_name>/deposit', methods=['PUT', 'POST'])
def deposit(wallet_name):
    '''
    Deposit money in wallet
    '''
    abort.if_wallet_doesnt_exist(
        wallet_name=wallet_name, 
        model=Wallet)
    abort.if_value_not_specified(arg='sum', request=request)

    ### checking amount provided (aka <adding>) ###
    adding = Decimal(request.args['sum'])
    adding = safe_round(adding)
    abort.if_negative_arg(adding, operation='deposit')
    abort.if_zero_amount(adding)

    # id checking
    # // id = get_id()
    # // abort.if_id_not_unique(id, idstorage)
    
    ### actual balance changing ###
    wallet = Wallet.query.filter(Wallet.name == wallet_name).first()
    old_balance = Decimal(str(wallet.balance))
    new_balance = old_balance + adding
    wallet.balance = new_balance
    db.session.commit()
    
    ### operation loading and commiting ###
    operation = operation_schema.load(
        dict(
            optype='deposit',
            sent_to=wallet_name,
            amount=adding,
            time=datetime.now().isoformat())
            )
    
    db.session.add(operation)
    db.session.commit()

    # registering
    # // reg = make_register(optype='deposit', amount=adding, id=id)
    
    resp = cook_response(
        app, {f'{wallet_name}:new_balance' : new_balance} 
        )
    
    return resp, 200

#
# transaction <from_wallet> <to_wallet>
#
@app.route('/v1/<from_wallet>/pay', methods=['PUT', 'POST'])
def transaction(from_wallet):
    '''
    Pay from one wallet to another
    '''
    ### pre-checkings ###
    abort.if_wallet_doesnt_exist(from_wallet, Wallet)
    abort.if_value_not_specified(  # where to pay
        arg='to', 
        request=request)      
    abort.if_value_not_specified(  # how much to pay
        arg='sum', 
        request=request)

    to_wallet = request.args['to']
    abort.if_wallet_doesnt_exist(to_wallet, Wallet)
    
    ### operation checkings ###
    amount = Decimal(request.args['sum'])
    amount = safe_round(amount)
    abort.if_balance_falls_below_zero(
        from_wallet=from_wallet, 
        value=amount,
        model=Wallet)
    abort.if_negative_arg(
        arg=amount, 
        operation='transaction')
    abort.if_zero_amount(amount)

    # id checking
    # id = get_id()
    # abort.if_id_not_unique(id, idstorage)

    ### changing balances ###
    # from_wallet
    wallet_1 = Wallet.query.filter(
        Wallet.name == from_wallet).first()
    old_balance_1 = Decimal(str(wallet_1.balance))
    new_balance_1 = old_balance_1 - amount
    wallet_1.balance = new_balance_1
    db.session.commit()

    # to_wallet
    wallet_2 = Wallet.query.filter(
        Wallet.name == to_wallet).first()
    old_balance_2 = Decimal(str(wallet_2.balance))
    new_balance_2 = old_balance_2 + amount
    wallet_2.balance = new_balance_2
    db.session.commit()
    
    ### making history ###

    operation = operation_schema.load(
        dict(
            optype='transaction',
            amount=amount,
            sent_to=to_wallet,
            get_from=from_wallet,
            time=datetime.now().isoformat())
            )
    db.session.add(operation)
    db.session.commit()

    ### getting actual balance of the donor wallet ###
    wallet_1 = \
        Wallet.query.filter(Wallet.name == from_wallet).first()
    act_balance = Decimal(str(wallet_1.balance))

    resp = cook_response(
        app=app,
        data={f'{from_wallet}:balance' : act_balance})
    
    return resp, 200

    
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
