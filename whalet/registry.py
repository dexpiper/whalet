'''
UNDER CONSTRUCTION

Tools to register operations and check if
id of an operation is unique.
'''

from datetime import datetime
from collections import deque
from uuid import uuid4

class IdStorage():
    '''
    A fast queue with 2 sets for storing id of 
    operations performed.

    Needed to protect wallets from doubling
    operations: if operation id is in storage,
    that operation has been performed already
    and should be declined.

    Id are added in sets: firstly in the left set,
    then in the right. When both sets are full, 
    left set would be removed, right set becomes 
    left, another empty set is appended to the right.

    - <limit> arg specify max len of each set
    
    Therefore, storage capacity:

    limit < storage capacity < 2*limit
    '''
    
    def __init__(self, limit=100):
        self.queue = deque(
            (set(), set()), 2)
        self.left_set = self.queue[0]
        self.right_set = self.queue[1]
        self.limit = limit
    
    def verify(self, id: str) -> bool:
        '''
        Check if <id> is in storage. 
        Return True if id is unique, else return
        False.
        '''
        if (id not in self.left_set) and (
            id not in self.right_set):
            
            self._append_it(id)
            return True
        
        else:
            return False
    
    def _append_it(self, id: str) -> None:
        '''
        First appending in left, when it is full -
        in right, then shifting.
        '''
        if len(self.left_set) < self.limit:
            self.left_set.add(id)
        elif len(self.right_set) < self.limit:
            self.right_set.add(id)
        else:
            self._shift()
            self.left_set.add(id)
    
    def _shift(self):
        '''
        left set deleted, right set becomes left
        '''
        self.queue.popleft()
        self.queue.append(set())

    def save(self):
        '''
        Save current state in file or
        in a database
        '''
        pass

    def load(self):
        '''
        Load last state from a file or
        from a database
        '''
        pass

def make_register(**kwargs) -> dict:
    '''
    Register an operation with given kwargs
    and return dct for appending in operations
    field in the database.

    Expected kwargs:
    - optype: Str (mandatory)
        optypes = ['creation', 'deposit', 
        'transaction']
    - (-)amount: Decimal()
        (mandatory for deposit and transaction)
            for sender < 0;
            for recepient > 0;
    - sent_to: Str
        (mandatory for transaction - sender)
    - get_from: Str
        (mandatory for transaction - recepient)
    - <id> and <time> kwargs could be specified 
        explicitly if needed.
    '''
    # operation types (optypes)
    optypes = ['creation', 'deposit', 'transaction']
    # checks
    if 'optype' not in kwargs:
        raise Exception('No operation type provided')
    if kwargs['optype'] not in optypes:
        raise Exception('Invalid optype')
    if kwargs['optype'] == (
        'transaction' or 'deposit'
    ) and 'amount' not in kwargs:
        raise Exception('Amount arg not specified')
    if kwargs['optype'] == 'transaction'\
            and (  ('sent_to' not in kwargs)
                and ('get_from' not in kwargs)):
        raise Exception('Recipient or sender not specified')
    
    if kwargs['optype'] == 'transaction'\
            and kwargs['amount'] < 0\
            and 'sent_to' not in kwargs:
        raise Exception('Recepient not specified')
    
    if kwargs['optype'] == 'transaction'\
            and kwargs['amount'] < 0\
            and 'get_from' in kwargs:
        raise Exception('Incoming transaction less zero')
    
    # changing sign for outcoming transaction
    if kwargs['optype'] == 'transaction'\
            and kwargs['amount'] > 0\
            and 'sent_to' in kwargs\
            and 'get_from' not in kwargs:
        kwargs['amount'] = kwargs['amount'] * -1

    # setting values
    if 'time' not in kwargs:
        kwargs['time'] = datetime.now().isoformat()
    if 'id' not in kwargs:
        kwargs['id'] = str(uuid4())

    return dict(**kwargs)

def get_id() -> str:
    '''
    Get uuid4() id in str form
    '''
    return str(uuid4())
