'''
Defining marshmallow Schemas
'''
from marshmallow import Schema, ValidationError, fields, post_load

# internal
from whalet import models


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
    id = fields.Str(dump_only=True)
    optype = fields.Str(validate=must_be_enum)
    time = fields.DateTime()
    amount = fields.Decimal(as_string=True)
    sent_to = fields.Str()
    get_from = fields.Str()

    @post_load
    def make_op(self, data, **kwargs):
        return models.Operation(**data)


class WalletSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    balance = fields.Decimal(as_string=True)
    password_hash = fields.Str(load_only=True)

    @post_load
    def make_wallet(self, data, **kwargs):
        return models.Wallet(**data)
