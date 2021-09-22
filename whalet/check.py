'''
Provides tools for checking conditions and aborting
with appropriate HTTPs codes and messages.

While aborting flask.abort is used.
'''
from decimal import Decimal
import string
from typing import Any

from flask import abort

# from whalet.registry import IdStorage


class Abort:
    '''
    Provides ready-to-use abort functions.

    Every function checks some condition and
    aborts session with appropriate code if
    the condition is True.
    '''
    def __init__(
            self,
            app,
            db):
        self.app = app
        # self.log = self.app.logger
        self.db = db

    #
    # Abort functions
    #
    def if_wallet_doesnt_exist(
            self,
            wallet_name: str,
            model: object):
        '''
        Abort if given wallet name doesn't exist
        '''
        c = self.db.query(
                model.id).filter_by(
                    name=wallet_name).scalar()
        if not c:
            abort(
                404, f"Wallet {wallet_name} does not exist"
            )

    def if_wallet_already_exists(
            self,
            wallet_name: str,
            model: object):
        '''
        Abort if given wallet name exists already
        '''
        c = self.db.query(
                model.id).filter_by(
                    name=wallet_name).scalar()
        if c:
            abort(
                409, f'Wallet {wallet_name} already exists.\
                     Try another name')

    def if_bad_wallet_name(self, arg: str):
        '''
        Wallet name limitations:

        - latin letters, numbers 0-9 and "-" and "_"
        - should start with a letter or a number
        - name length should be less or equal 14 and more or equal 4

        '''
        # name length
        if len(arg) > 14:
            abort(
                400,
                'Bad wallet name. Too long'
                )

        if len(arg) < 4:
            abort(
                400,
                'Bad wallet name. Too short'
                )

        # name chars
        allowed = set(
            string.ascii_lowercase
            + string.ascii_uppercase
            + string.digits
            + '-' + '_'
        )
        good_name = set(arg) <= allowed
        if not good_name:
            abort(
                400,
                'Bad wallet name. Only letters, digits \
                    and "-", "_" chars allowed.'
                )

        # name start chars
        if arg.startswith('-') or arg.startswith('_'):
            abort(
                400,
                'Bad wallet name. Should start with a letter or a digit'
                )

    def if_value_not_specified(
            self,
            arg: str,
            request: object,
            code=400,
            message='No value specifiend for the operation'):
        '''
        Abort if argument string could not be found
        in request.args
        '''
        try:
            request.args[arg]
        except KeyError:
            self.app.logger.info(
                f'Could not find {arg} in request.args')
            abort(code, message)

    def if_balance_falls_below_zero(
            self,
            from_wallet: str,
            value: Decimal or float,
            model: object):
        '''
        Abort if balance of given wallet
        dives below zero after initialized
        operation.
        '''
        balance = self.db.query(model).filter(
            model.name == from_wallet).first().balance
        balance = Decimal(str(balance))

        if balance - Decimal(value) < Decimal('0'):
            abort(
                409,
                f'Not enough money in wallet {from_wallet}'
                )

    def if_negative_arg(
            self,
            arg: Decimal or float,
            operation=None):
        '''
        Abort if an argument is negative
        '''
        if arg < Decimal('0'):
            err_message = 'Negative argument is not allowed'
            if operation:
                ' '.join(
                    (err_message, f'during {operation}')
                )
            abort(400, err_message)

    def if_zero_amount(self, arg: Decimal or float):
        if arg < Decimal('0.01'):
            abort(
                400, 'Operation sum should be more or equal 0.01'
            )

    def if_not_numeric(self, arg: Any):
        try:
            float(arg)
        except ValueError:
            abort(
                400, f'Argument {arg}: wrong format (expected numeric)'
            )

    def if_bad_password(self, pwd: str):
        '''
        Check password
        '''
        # pass length
        if len(pwd) > 14:
            abort(
                400,
                'Bad password. Too long'
                )

        if len(pwd) < 6:
            abort(
                400,
                'Bad password. Too short'
                )

        # name chars
        allowed = set(
            string.ascii_lowercase
            + string.ascii_uppercase
            + string.digits
            + '-' + '_' + '&' + '%'
            + ':' + '#' + '@' + '?'
            + '*' + '!' + '?' + '>'
            + '<' + '.' + ',' + '~'
        )
        good_name = set(pwd) <= allowed
        if not good_name:
            abort(
                400,
                'Bad password. Unsupported chars'
                )

    def if_user_doesnt_exist(
            self,
            username: str,
            model: object):
        '''
        Abort if username doesn't exist
        '''
        c = self.db.query(
                model.id).filter_by(
                    name=username).scalar()
        if not c:
            abort(
                404, f"User {username} does not exist. Check login"
            )

    def if_token_incorrect(
            self,
            token: str,
            master_token: str):
        if not token == master_token:
            abort(
                401, "Token incorrect"
            )
