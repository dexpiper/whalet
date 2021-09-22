'''
App routes and main logic defined here.

Module should be imported in app_context() only because of
the blueprint architecture:

with app.app_context():
    from whalet import routes

Functions use SQLAlchemy session object (db variable)
and an instance of custom Abort class which provides handy
abort scenarios if user request does not meet some pre-
requisites.

This objects - db and abort - module gets from app_context.
'''

# Python Standard Library
from datetime import datetime
from decimal import Decimal

# Flask
from flask import Blueprint
from flask import abort as flask_abort
from flask import request
from flask import current_app
from flask_httpauth import HTTPBasicAuth

# internal modules
from whalet import models, schema
from whalet.helpers import (change_sign, cook_response,
                            make_query, represent, safe_round)


#
# SETTING
#
app = current_app
with app.app_context():
    db = current_app.config['DATABASE_SESSION']
    abort = current_app.config['ABORT_HELPER']
    master_token = app.config['MASTER_TOKEN']
    main = Blueprint('main', __name__)
    auth = HTTPBasicAuth()

# setting marshmallow schemas

operation_schema = schema.OperationSchema()
operations_schema = schema.OperationSchema(many=True)
wallet_schema = schema.WalletSchema()
wallets_schema = schema.WalletSchema(many=True)


# setting authentication
@auth.verify_password
def verify_password(username, password):

    if not password or not username:
        return False

    wallet = db.query(
                models.Wallet).filter_by(
                    name=username).scalar()

    if not wallet:
        current_app.logger.debug(f'Auth: No wallet {username} found')
        abort.if_user_doesnt_exist(
            username=username,
            model=models.Wallet
        )

    if models.Wallet.verify_password(db, username, password):
        return wallet

    else:
        return False


# token auth
def master_token_required(func):
    '''
    Decorator to ask master token for token-protected
    operations like deposit and wallets inspection.
    '''
    def function_wrapper(*args, **kwargs):
        abort.if_value_not_specified(
            arg='token', request=request,
            code=401,
            message='Anauthorized')
        token = request.args['token']
        abort.if_token_incorrect(
            token=token, master_token=master_token)
        return func(*args, **kwargs)
    function_wrapper.__name__ = func.__name__
    return function_wrapper


#
#  API
#
@main.route('/', methods=['GET'])
def hello():
    '''
    Say hello
    '''
    app.logger.info('Got test request. Returning answer')
    resp = cook_response(app, {'Whaletapp': 'Welcome!'})
    return resp, 200


# Get wallet list
@main.route('/v1/wallets', methods=['GET'])
@master_token_required
def get_wallets():
    '''
    Get all the wallets and their balances
    '''
    wallets = db.query(models.Wallet).all()
    result = wallets_schema.dump(wallets)

    resp = cook_response(app, {'wallets': result})

    return resp, 200


# create a wallet
@main.route('/v1/create', methods=['POST'])
def create_wallet():
    '''
    Creating a new wallet with 0 balance
    '''
    abort.if_value_not_specified(
        arg='name', request=request)
    abort.if_value_not_specified(
        arg='pwd', request=request)
    wallet_name = request.args['name']
    password = request.args['pwd']
    abort.if_wallet_already_exists(
        wallet_name=wallet_name,
        model=models.Wallet
        )
    abort.if_bad_wallet_name(arg=wallet_name)
    abort.if_bad_password(pwd=password)
    try:
        app.logger.info('Trying to load new user into Wallet')
        wallet = wallet_schema.load(
            dict(
                name=wallet_name,
                balance=Decimal('0'),
                password_hash=models.Wallet.hash_password(
                    password=password)
                )
        )
    except Exception as exc:
        app.logger.info(f'{exc}')
        flask_abort(500, 'Error during wallet creation')

    operation = operation_schema.load(
        dict(
            optype='creation',
            time=datetime.now().isoformat(),
            sent_to=wallet_name
            )
        )

    db.add(wallet)
    db.add(operation)
    db.commit()

    resp = cook_response(
        app,
        {f'{wallet_name}:created': 'true'}
        )

    return resp, 201


# get balance for a wallet
@main.route('/v1/balance', methods=['GET'])
@auth.login_required
def get_balance():
    '''
    Get balance for given wallet
    '''
    wallet_name = auth.current_user().name

    balance = db.query(models.Wallet).filter(
        models.Wallet.name == wallet_name
    ).first()

    # balance: str
    balance = represent(balance.balance)
    resp = cook_response(
        app,
        {f'{wallet_name}:balance': balance})

    return resp, 200


# change password for user
@main.route('/v1/change_pass', methods=['PUT', 'POST'])
@auth.login_required
def change_password():
    '''
    Change password for user
    '''
    wallet_name = auth.current_user().name
    abort.if_value_not_specified(
        arg='pwd', request=request)
    password = request.args['pwd']
    abort.if_bad_password(pwd=password)

    try:
        app.logger.info('Trying to change password')
        db.query(models.Wallet).filter(
            models.Wallet.name == wallet_name).update(
                {
                    models.Wallet.password_hash:
                        models.Wallet.hash_password(password)
                }
        )
    except Exception as exc:
        app.logger.info(f'{exc}')
        flask_abort(500, 'Error during changing password')

    resp = cook_response(
        app,
        {f'{wallet_name}:password': 'changed'})

    return resp, 200


# get op history for a wallet
@main.route('/v1/history', methods=['GET'])
@main.route('/v1/history/page/<int:page>', methods=['GET'])
@auth.login_required
def get_history(page=1):
    '''
    Get history for given wallet
    '''
    wallet_name = auth.current_user().name

    the_query = make_query(
        db=db,
        wallet_name=wallet_name,
        model=models.Operation)

    # TODO(Alex): pagination with Query obj does not work
    # need some pure SQL implementation

    result = operations_schema.dump(the_query.all())
    result = change_sign(result, wallet_name)
    resp = cook_response(
        app,
        {f'{wallet_name}:history': result}
        )

    return resp, 200


# deposit money to wallet
@main.route('/v1/deposit', methods=['PUT', 'POST'])
@master_token_required
def deposit():
    '''
    Deposit money in wallet
    '''
    abort.if_value_not_specified(arg='to', request=request)
    wallet_name = request.args['to']
    abort.if_value_not_specified(arg='sum', request=request)

    # checking amount provided (aka <adding>)
    provided_sum = request.args['sum']
    abort.if_not_numeric(provided_sum)
    adding = Decimal(provided_sum)
    adding = safe_round(adding)
    abort.if_negative_arg(adding, operation='deposit')
    abort.if_zero_amount(adding)

    # actual balance changing
    wallet = db.query(models.Wallet).filter(
        models.Wallet.name == wallet_name).first()
    old_balance = Decimal(str(wallet.balance))
    new_balance = old_balance + adding
    wallet.balance = new_balance
    db.commit()

    # operation loading and commiting
    operation = operation_schema.load(
        dict(
            optype='deposit',
            sent_to=wallet_name,
            amount=adding,
            time=datetime.now().isoformat())
            )

    db.add(operation)
    db.commit()

    resp = cook_response(
        app, {f'{wallet_name}:new_balance': new_balance}
        )

    return resp, 200


# transaction <from_wallet> <to_wallet>
@main.route('/v1/pay', methods=['PUT', 'POST'])
@auth.login_required
def transaction():
    '''
    Pay from one wallet to another
    '''
    from_wallet = auth.current_user().name

    # pre-checkings
    abort.if_value_not_specified(  # where to pay
        arg='to',
        request=request
    )
    to_wallet = request.args['to']
    abort.if_wallet_doesnt_exist(to_wallet, models.Wallet)
    abort.if_value_not_specified(  # how much to pay
        arg='sum',
        request=request)

    # operation checkings
    amount = request.args['sum']
    abort.if_not_numeric(amount)
    amount = safe_round(Decimal(amount))
    abort.if_balance_falls_below_zero(
        from_wallet=from_wallet,
        value=amount,
        model=models.Wallet)
    abort.if_negative_arg(
        arg=amount,
        operation='transaction')
    abort.if_zero_amount(amount)

    # changing balances:
    db.query(models.Wallet).filter(
        models.Wallet.name == from_wallet).update(
            {models.Wallet.balance: models.Wallet.balance - amount}
        )

    db.query(models.Wallet).filter(
        models.Wallet.name == to_wallet).update(
            {models.Wallet.balance: models.Wallet.balance + amount}
        )

    # making history:
    operation = operation_schema.load(
        dict(
            optype='transaction',
            amount=amount,
            sent_to=to_wallet,
            get_from=from_wallet,
            time=datetime.now().isoformat())
            )
    db.add(operation)
    db.commit()

    # getting actual balance of the donor wallet
    wallet_1 = db.query(models.Wallet).filter(
            models.Wallet.name == from_wallet).first()
    act_balance = Decimal(str(wallet_1.balance))

    resp = cook_response(
        app=app,
        data={f'{from_wallet}:balance': act_balance}
    )

    return resp, 200
