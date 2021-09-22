'''
Helpful instruments for tests
'''
from collections import namedtuple
from base64 import b64encode


def get_headers(name, password, encoding='utf-8'):
    '''
    Return headers for request with given name
    and password.
    '''
    def encode_name_and_password(name, password, encoding):
        '''
        Code username and password for request
        '''
        result = b64encode(
            bytes(
                f'{name}:{password}',
                encoding
            )).decode(encoding)

        return result

    name_and_pwd = encode_name_and_password(name, password, encoding)
    credentials = f'Basic {name_and_pwd}'
    headers = {'Authorization': f'{credentials}'}
    return headers


# named tuple for RequestData
RequestData = namedtuple(
    'RequestData', ['from_wallet', 'to_wallet', 'headers'])
