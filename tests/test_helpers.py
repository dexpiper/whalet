from decimal import Decimal

from whalet.helpers import change_sign, safe_round, represent


def test_safe_round():
    n = Decimal('1.19999999999999911199')
    assert safe_round(n) == Decimal('1.19')
    n = Decimal('128')
    assert safe_round(n) == Decimal('128')
    n = Decimal('0.01')
    assert safe_round(n) == Decimal('0.01')
    assert safe_round(Decimal('0')) == Decimal('0')
    assert safe_round(Decimal('0.00000000000000')) == Decimal('0')


def test_represent():
    assert represent(Decimal('2')) == '2.00'
    assert represent(Decimal('156')) == '156.00'
    assert represent(Decimal('0.01')) == '0.01'
    assert represent(Decimal('12891.1')) == '12891.10'
    assert represent(Decimal('0')) == '0.00'


def test_change_sign():
    lst = [
            {  # this is outcoming transaction for Tester
                'sent_to': 'spam007',
                'get_from': 'Tester',
                'optype': 'transaction',
                'amount': '42.09'
            },
            {  # this is incoming transaction for Tester
                'sent_to': 'Tester',
                'get_from': 'KingArthur1957',
                'optype': 'transaction',
                'amount': '42.09'
            }
        ]
    new_lst = change_sign(lst, 'Tester')
    assert new_lst[0]['amount'] == '-42.09'  # sign changed
    assert new_lst[1]['amount'] == '42.09'   # sign unchanged
