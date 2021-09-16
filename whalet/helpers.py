'''
Useful functions to leverage responses
'''
import json
from decimal import Decimal
from math import trunc

from flask import Flask, request
from sqlalchemy import or_
from sqlalchemy.orm import session


def cook_response(app: 'Flask', data, format='json'):
    '''
    Slightly modified json.dumps(). Returns
    flask response with default params
    dealing with Decimal numbers.
    '''
    def decimal_json_default(obj):
        if isinstance(obj, Decimal):
            return str(obj)

    if format == 'json':
        func = decimal_json_default
    elif format == 'xml':
        # not implemented
        pass

    resp = app.response_class(
        f"{json.dumps(data, default=func)}",
        mimetype="application/json"
        # app.config["JSONIFY_MIMETYPE"],
    )

    return resp


def safe_round(arg: Decimal):
    '''
    Truncate given number up to 2 digits after
    delimiter (without any rounding):

    >>> safe_round(15.0199999999)
    >>> 15.01
    '''
    arg = arg * 100
    arg = trunc(arg)
    arg = Decimal(str(arg / 100))
    return arg


def represent(arg: Decimal) -> str:
    '''
    Make string from Decimal number, with
    2 digits after delimiter:

    >>> represent(Decimal('42'))
    >>> 42.00
    '''
    arg = '{:.2f}'.format(arg)
    return arg


def change_sign(result, wallet_name):
    '''
    Change sign (from plus to minus) for
    outcoming transactions.
    '''
    for el in result:
        if (
            el['get_from'] == wallet_name
        ) and (
            el['optype'] == 'transaction'
        ):
            el['amount'] = '-' + el['amount']

    return result


def make_query(
        db: session,
        wallet_name: str,
        model: object):
    '''
    Get ordered query object of all operations
    '''
    result = db.query(model).filter(
        or_(
            model.sent_to == wallet_name,
            model.get_from == wallet_name
        )).order_by(model.time)
    return result


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


def request_constr(
        method='GET',
        adr='http://127.0.0.1:5000/v1',
        addition='',
        **kwargs):
    '''
    Depricated.
    Helps to form requests for curl
    '''
    start = f"""curl -X {method}"""
    if not addition.startswith('/'):
        addition = '/' + addition
    address = start + " '" + adr + addition
    if kwargs:
        address += '?'
        for i, j in kwargs.items():
            s = f'{i}={j}&'
            address += s
        address = address[:-1] + "'"
    return address
