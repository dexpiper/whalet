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

# internal modules
from whalet import models, schema
from whalet.helpers import (change_sign, cook_response,
                            make_query, represent, safe_round,
                            shutdown_server)

# // under construction
# // from whalet.registry import IdStorage, make_register, get_id


#
# SETTING
#
app = current_app
with app.app_context():
    db = current_app.config['DATABASE_SESSION']
    abort = current_app.config['ABORT_HELPER']
    main = Blueprint('main', __name__)

# setting marshmallow schemas

operation_schema = schema.OperationSchema()
operations_schema = schema.OperationSchema(many=True)
wallet_schema = schema.WalletSchema()
wallets_schema = schema.WalletSchema(many=True)


#
#  API
#
@main.route('/', methods=['GET'])
def hello():
    '''
    Say hello
    '''
    resp = cook_response(app, {'hello': 'world!'})
    return resp, 200


# Get wallet list
@main.route('/v1/wallets', methods=['GET'])
def get_wallets():
    '''
    Get all the wallets and their balances
    '''
    wallets = db.query(models.Wallet).all()
    result = wallets_schema.dump(wallets)

    resp = cook_response(app, {'wallets': result})

    return resp, 200


# create a wallet
@main.route('/v1/create/<wallet_name>', methods=['POST'])
def create_wallet(wallet_name):
    '''
    Creating a new wallet with 0 balance
    '''
    abort.if_wallet_already_exists(
        wallet_name=wallet_name,
        model=models.Wallet
        )
    abort.if_bad_wallet_name(arg=wallet_name)
    try:
        wallet = wallet_schema.load(
            dict(name=wallet_name, balance=Decimal('0'))
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
@main.route('/v1/<wallet_name>/balance', methods=['GET'])
def get_balance(wallet_name):
    '''
    Get balance for given wallet
    '''
    abort.if_wallet_doesnt_exist(
        wallet_name=wallet_name,
        model=models.Wallet)
    balance = db.query(models.Wallet).filter(
        models.Wallet.name == wallet_name
    ).first()

    # balance.balance: Decimal
    app.logger.info(f'Balance: {balance.balance}')

    # balance: str
    balance = represent(balance.balance)
    resp = cook_response(
        app,
        {f'{wallet_name}:balance': balance})

    return resp, 200


# get op history for a wallet
@main.route('/v1/<wallet_name>/history', methods=['GET'])
@main.route('/v1/<wallet_name>/history/page/<int:page>', methods=['GET'])
def get_history(wallet_name, page=1):
    '''
    Get history for given wallet
    '''
    abort.if_wallet_doesnt_exist(
        wallet_name=wallet_name,
        model=models.Wallet)

    the_query = make_query(
        db=db,
        wallet_name=wallet_name,
        model=models.Operation)

    # TODO(Alex): pagination with Query obj does not work
    # need some pure SQL implementation
    '''paginator = the_query.paginate(
                page, per_page=15, error_out=False)

    total_pages = paginator.pages

    abort.if_page_not_exist(
        asked_page=page,
        total_pages=total_pages)

    page_items = paginator.items

    if len(page_items) < 2:
        result = operation_schema.dump(
            page_items)
    else:
        result = operations_schema.dump(
            page_items)'''

    # TODO(Alex): to be changed, temporary solution
    result = operations_schema.dump(the_query.all())
    result = change_sign(result, wallet_name)
    resp = cook_response(
        app,
        {f'{wallet_name}:history': result}
        )

    '''resp = cook_response(
        app,
        {f'page:{page}of{total_pages}': result}
        )'''

    return resp, 200


# deposit money to wallet
@main.route('/v1/<wallet_name>/deposit', methods=['PUT', 'POST'])
def deposit(wallet_name):
    '''
    Deposit money in wallet
    '''
    abort.if_wallet_doesnt_exist(
        wallet_name=wallet_name,
        model=models.Wallet)
    abort.if_value_not_specified(arg='sum', request=request)

    # checking amount provided (aka <adding>)
    provided_sum = request.args['sum']
    abort.if_not_numeric(provided_sum)
    adding = Decimal(provided_sum)
    adding = safe_round(adding)
    abort.if_negative_arg(adding, operation='deposit')
    abort.if_zero_amount(adding)

    # id checking
    # // id = get_id()
    # // abort.if_id_not_unique(id, idstorage)

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

    # registering
    # // reg = make_register(optype='deposit', amount=adding, id=id)

    resp = cook_response(
        app, {f'{wallet_name}:new_balance': new_balance}
        )

    return resp, 200


# transaction <from_wallet> <to_wallet>
@main.route('/v1/<from_wallet>/pay', methods=['PUT', 'POST'])
def transaction(from_wallet):
    '''
    Pay from one wallet to another
    '''
    # pre-checkings
    abort.if_wallet_doesnt_exist(from_wallet, models.Wallet)
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

    # id checking
    # id = get_id()
    # abort.if_id_not_unique(id, idstorage)

    # changing balances:
    # from_wallet
    wallet_1 = db.query(models.Wallet).filter(
        models.Wallet.name == from_wallet).first()
    old_balance_1 = Decimal(str(wallet_1.balance))
    new_balance_1 = old_balance_1 - amount
    wallet_1.balance = new_balance_1
    db.commit()

    # to_wallet
    wallet_2 = db.query(models.Wallet).filter(
        models.Wallet.name == to_wallet).first()
    old_balance_2 = Decimal(str(wallet_2.balance))
    new_balance_2 = old_balance_2 + amount
    wallet_2.balance = new_balance_2
    db.commit()

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


# Shutdown command
@main.route('/shutdown', methods=['GET', 'PUT'])
def shutdown():
    '''
    Shutting server down
    '''
    shutdown_server()
    return 'Server shutting down...'
