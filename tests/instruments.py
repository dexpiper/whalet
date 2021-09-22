'''
Helpful instruments for tests
'''

from base64 import b64encode


def encode_name_and_password(name, password):

    result = b64encode(
        bytes(
            f'{name}:{password}',
            'utf-8'
        )).decode('utf-8')

    return result
