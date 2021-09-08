'''
Useful functions to leverage responses
'''
from decimal import Decimal
import json

from flask import Flask

from whalet.data import data

#
# making response from data with Decimal
#
def cook_response(app: Flask, data, format='json'):
    '''
    Make flask response with respect of special
    json.dumps default params dealing with
    Decimal numbers in dict.
    '''
    def decimal_json_default(obj):
        if isinstance(obj, Decimal):
            return float(obj)

    if format == 'json':
        func = decimal_json_default
    elif format == 'xml':
        # not implemented
        pass
    
    resp = app.response_class(
        f"{json.dumps(data, default=func)}\n",
        mimetype=app.config["JSONIFY_MIMETYPE"],
    )

    return resp

def safe_round(arg: Decimal):
    return round(arg, 2)

# depricated
def transfer(
        from_wallet: str,
        to_wallet: str,
        amount: Decimal):
    balance_from = data['wallets'][from_wallet]['balance']
    balance_to = data['wallets'][to_wallet]['balance']
    balance_from -= amount
    balance_to += amount
    data['wallets'][from_wallet]['balance'] = balance_from
    data['wallets'][to_wallet]['balance'] = balance_to
    return balance_from, balance_to

