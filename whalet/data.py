'''
DEPRICATED

'''

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

# example dictionary
data = {
    'wallets' : {
            'Sam' : {
                'balance' : Decimal(0),
                'operations' : []
                }, 
            'Alice' : {
                'balance' : Decimal(0),
                'operations' : []
                }, 
            'Bob' : {
                'balance' : Decimal(0),
                'operations' : []
                },
            'Alex' : {
                'balance' : Decimal(0),
                'operations' : []
                },
        }
    }

_operation_pattern = {
    'time'    : '',                # datetime.now(),
    'optype'    : '',              # creation, deposit, transaction
#   'amount'  : 0                    Decimal()
#   'sent_to' : '',                  str(wallet_name)
#   'get_from': '',                  str(wallet_name)
    'id'      : ''                 # str(uuid4())
    }

for key in data['wallets'].keys():
    pattern = _operation_pattern
    pattern['time'] = datetime.now().isoformat()
    pattern['optype'] = 'creation'
    pattern['id'] = str(uuid4())
    data['wallets'][key]['operations'].append(pattern)
