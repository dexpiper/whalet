import json
import os
import tempfile
from datetime import datetime
from decimal import Decimal
import html

from pytest import fixture
from pytest import mark

from whalet import models
from whalet.check import Abort
from whalet.database import Database
from whalet.factory import create_app
from tests.instruments import get_headers


@fixture(scope='module')
def app():
    '''
    Create test app
    '''
    # temporary db and path
    db_fd, db_path = tempfile.mkstemp()
    db_path = 'sqlite:///' + db_path

    # test database
    TEST_URI = db_path
    global MASTER_TOKEN
    MASTER_TOKEN = 'whalesome'

    app = create_app()
    app.config['TESTING'] = True
    app.testing = True
    app.config['SQLALCHEMY_DATABASE_URI'] = TEST_URI
    app.config['MASTER_TOKEN'] = MASTER_TOKEN
    yield app

    # cleaning up
    os.close(db_fd)
    # os.unlink(db_path)


@fixture(scope='module')
def dbase(app):
    '''
    Make test database
    '''
    with app.app_context():
        url = app.config['SQLALCHEMY_DATABASE_URI']
    dbase = Database(url=url)
    yield dbase


@fixture(scope='module')
def tst_engine(dbase):
    tst_engine = dbase.engine
    yield tst_engine


@fixture(scope='module')
def db(dbase):
    db = dbase.create_session()
    yield db


@fixture(scope='module')
def client(app, db, tst_engine):
    '''
    Make test client
    '''
    abort = Abort(app, db)
    app.config['DATABASE_SESSION'] = db
    app.config['ABORT_HELPER'] = abort

    with app.test_client() as client:
        with app.app_context():
            from whalet import routes
            app.register_blueprint(routes.main)
            models.Base.metadata.create_all(bind=tst_engine)
        yield client


@fixture(scope='module')
def create_wallets(app, db):
    '''
    Create wallets for testing
    '''
    with app.app_context():

        from whalet.routes import operation_schema, wallet_schema

        # create wallets with common password
        usernames = ['Alex', 'Alice', 'Bob', 'Ann']
        global common_password
        common_password = '123456789test'

        for name in usernames:
            wallet = wallet_schema.load(
                dict(
                    name=name,
                    balance=Decimal('0'),
                    password_hash=models.Wallet.hash_password(
                        password=common_password)
                )
            )
            operation = operation_schema.load(
                dict(
                    optype='creation',
                    time=datetime.now().isoformat(),
                    sent_to=name
                    )
                )
            db.add(wallet)
            db.add(operation)
        db.commit()
        return True


def test_hello(client):
    rv = client.get('/')
    assert rv.status_code == 200


def test_users_return(client):
    rv = client.get(f'/v1/wallets?token={MASTER_TOKEN}')
    assert rv.status_code == 200


def test_users_without_token(client):
    rv = client.get('/v1/wallets')
    assert rv.status_code == 401
    assert 'anauthorized' in str(rv.data).lower()


def test_users_with_bad_token(client):
    rv = client.get('/v1/wallets?token=baconeggsspamspamspam')
    assert rv.status_code == 401
    assert 'token incorrect' in str(rv.data).lower()


@mark.parametrize('name', ['Alex', 'Alice', 'Bob', 'Ann'])
def test_users_exist(client, create_wallets, name):

    # sanity check
    assert create_wallets

    rv = client.get(f'/v1/wallets?token={MASTER_TOKEN}')
    assert name in str(rv.data)


@mark.parametrize('fake_name', ['KingArthur', 'bacon41', 'Reachy'])
def test_users_does_not_exist(
        client,
        create_wallets,
        fake_name):

    assert create_wallets

    rv = client.get(f'/v1/wallets?token={MASTER_TOKEN}')
    assert fake_name not in str(rv.data)


@mark.parametrize('name', ['Alex', 'Alice', 'Bob', 'Ann'])
def test_get_balance_for_existing_user(
        client,
        create_wallets,
        name):

    assert create_wallets

    headers = get_headers(name=name,
                          password=common_password)

    rv = client.get('/v1/balance', headers=headers)
    assert rv.status_code == 200
    balance = json.loads(rv.data)[f'{name}:balance']
    assert balance == '0.00'


@mark.parametrize('fake_name', ['KingArthur', 'Bacon', 'Eggs'])
def test_get_balance_for_non_existing_user(
        client,
        create_wallets,
        fake_name):

    assert create_wallets

    headers = get_headers(name=fake_name,
                          password=common_password)

    rv = client.get('/v1/balance', headers=headers)
    assert rv.status_code == 404

    # using html.unescape due to HTML hash entites in response
    assert f"{fake_name} does not exist"\
        in html.unescape(str(rv.data))


def test_create_user_bad_named(client):

    bad_names = [
        ' 1235',              # a space char
        'b@con&eggs12',       # unsupported chars
        'θatße',              # unsupported chars
        'MobyDick777.',       # period in name
        '-hellowhale',        # starts with '-'
        '_whoa098',           # starts with '_'
        'getouttahere19710',  # len(name) > 14
        'Abc'                 # len(name) < 4
    ]
    for name in bad_names:
        rv = client.post(f'/v1/create?name={name}&pwd={common_password}')
        assert rv.status_code == 400
        assert 'bad wallet name' in str(rv.data).lower()


def test_create_new_user(client):

    # perfect name for a wallet
    name = 'Reachy'
    rv = client.post(f'/v1/create?name={name}&pwd={common_password}')
    assert rv.status_code == 201
    assert f'"{name}:created": "true"' in str(rv.data)


def test_get_balance_new_user(client):

    name = 'Reachy'
    headers = get_headers(name=name,
                          password=common_password)

    rv = client.get('/v1/balance', headers=headers)
    assert rv.status_code == 200
    json_to_dict = json.loads(rv.data)

    # assert that newly created user has 0 balance
    assert json_to_dict[f'{name}:balance'] == '0.00'


def test_make_deposit_without_token(client):
    rv = client.put('/v1/deposit?to=Reachy')
    assert rv.status_code == 401
    assert 'anauthorized' in str(rv.data).lower()


def test_make_deposit_with_bad_token(client):
    bad_token = 'baconeggsspamspamspam'
    rv = client.put(f'/v1/deposit?to=Reachy&token={bad_token}')
    assert rv.status_code == 401
    assert 'token incorrect' in str(rv.data).lower()


def test_make_deposit_without_proper_arg(client):

    name = 'Reachy'

    # <sum> arg has not been provided
    rv = client.put(f'/v1/deposit?to={name}&token={MASTER_TOKEN}')
    assert rv.status_code == 400,\
        'Did not return 400 when no <sum> arg was provided'

    # <sum> arg has not been provided (other args wihout valid names)
    # but with good token
    rv = client.put(
        f'/v1/deposit?parrot=DeadTotally0&bacon=SPAM&token={MASTER_TOKEN}')
    assert rv.status_code == 400,\
        'Did not return 400 whith no accurate arg name given'

    # wrong arg format
    rv = client.put(
        f'/v1/deposit?to={name}&sum=SPAMSPAMSPAM.42&token={MASTER_TOKEN}')
    assert rv.status_code == 400,\
        'Did not return 400 with inappropriate arg (non-numerical)'


def test_make_deposit(client):

    name = 'Reachy'
    rv = client.put(
        f'/v1/deposit?to={name}&sum=42.221001&token={MASTER_TOKEN}')
    assert rv.status_code == 200

    # first deposit (+42.22)
    headers = get_headers(name=name,
                          password=common_password)
    rv = client.get('/v1/balance', headers=headers)
    assert rv.status_code == 200
    new_balance = json.loads(rv.data)[f'{name}:balance']
    assert str(new_balance) == '42.22'

    # second deposit (+15092.00)
    rv = client.put(
        f'/v1/deposit?to={name}&sum=15092&token={MASTER_TOKEN}')
    assert rv.status_code == 200
    rv = client.get('/v1/balance', headers=headers)
    new_balance = json.loads(rv.data)[f'{name}:balance']
    assert str(new_balance) == '15134.22'


def test_get_history_operations_first(client):

    # Reachy should have 3 records:
    # creation + deposit 42.22 + deposit +15092.00
    name = 'Reachy'
    headers = get_headers(name=name,
                          password=common_password)
    rv = client.get('/v1/history', headers=headers)
    assert rv.status_code == 200
    history = json.loads(rv.data)[f'{name}:history']
    assert len(history) == 3

    # Alice has one record: creation
    name = 'Alice'
    headers = get_headers(name=name,
                          password=common_password)
    rv = client.get('/v1/history', headers=headers)
    assert rv.status_code == 200
    history = json.loads(rv.data)[f'{name}:history']
    assert len(history) == 1

'''
def test_make_transaction_fake_wallet(client):

    from_wallet = 'Reachy'
    to_wallet = 'Alice'
    fake_wallet = 'King_Arthur'

    # transaction from fake wallet
    rv = client.put(f'/v1/{fake_wallet}/pay?to={to_wallet}')
    assert rv.status_code == 404
    assert f"Wallet {fake_wallet} doesn't exist"\
        in html.unescape(str(rv.data))

    # transaction to fake wallet
    rv = client.put(f'/v1/{from_wallet}/pay?to={fake_wallet}')
    assert rv.status_code == 404
    assert f"Wallet {fake_wallet} doesn't exist"\
        in html.unescape(str(rv.data))


def test_make_transaction_without_arg(client):

    from_wallet = 'Reachy'
    to_wallet = 'Alice'

    # transaction without amount or destination specified
    rv = client.put(f'/v1/{from_wallet}/pay?to={to_wallet}')
    assert rv.status_code == 400
    rv = client.put(f'/v1/{from_wallet}/pay?sum=123.14')
    assert rv.status_code == 400


def test_make_transaction_with_wrong_argtype(client):

    from_wallet = 'Reachy'
    to_wallet = 'Alice'

    # transactions with wrong argument types:
    # letters in <sum> arg
    rv = client.put(f'/v1/{from_wallet}/pay?to={to_wallet}&sum=SPamm1')
    assert rv.status_code == 400
    assert "wrong format (expected numeric)"\
        in html.unescape(str(rv.data))

    # two dots in arg
    rv = client.put(f'/v1/{from_wallet}/pay?to={to_wallet}&sum=123.01.1')
    assert rv.status_code == 400
    assert "wrong format (expected numeric)"\
        in html.unescape(str(rv.data))


def test_make_transaction_with_negative_argument(client):

    from_wallet = 'Reachy'
    to_wallet = 'Alice'

    # negative arg
    rv = client.put(f'/v1/{from_wallet}/pay?to={to_wallet}&sum=-0.18')
    assert rv.status_code == 400
    assert "negative argument" in html.unescape(str(rv.data)).lower()


def test_make_transaction_with_zero_argument(client):

    from_wallet = 'Reachy'
    to_wallet = 'Alice'

    # zero arg
    rv = client.put(f'/v1/{from_wallet}/pay?to={to_wallet}&sum=0')
    assert rv.status_code == 400
    assert "Operation sum should be more or equal 0.01"\
        in html.unescape(str(rv.data))

    # arg --> zero
    rv = client.put(f'/v1/{from_wallet}/pay?to={to_wallet}&sum=0.0001')
    assert rv.status_code == 400
    assert "Operation sum should be more or equal 0.01"\
        in html.unescape(str(rv.data))


def test_make_transaction_without_money(client):

    from_wallet = 'Alice'
    to_wallet = 'Reachy'

    # Alice has no money yet, but tries to pay Reachy
    rv = client.put(f'/v1/{from_wallet}/pay?to={to_wallet}&sum=41.01')
    assert rv.status_code == 409
    assert f"Not enough money in wallet {from_wallet}"\
        in html.unescape(str(rv.data))


def test_make_valid_transaction(client):

    from_wallet = 'Reachy'
    to_wallet = 'Alice'

    # Reachy makes perfectly valid transaction (but stingy)
    rv = client.put(f'/v1/{from_wallet}/pay?to={to_wallet}&sum=1.01')
    assert rv.status_code == 200


def test_balances_after_first_transaction(client):

    from_wallet = 'Reachy'
    to_wallet = 'Alice'

    # Reachy should become 1.01 less reach (before 15134.22)
    rv = client.get(f'/v1/{from_wallet}/balance')
    assert rv.status_code == 200
    reachy_balance = json.loads(rv.data)[f'{from_wallet}:balance']
    assert str(reachy_balance) == '15133.21'

    # Alice should asquire unbelievable wealth
    rv = client.get(f'/v1/{to_wallet}/balance')
    assert rv.status_code == 200
    alice_balance = json.loads(rv.data)[f'{to_wallet}:balance']
    assert str(alice_balance) == '1.01'


def test_get_history_operations_second(client):

    # Reachy has +1 operation in history
    name = 'Reachy'
    rv = client.get(f'/v1/{name}/history')
    assert rv.status_code == 200
    history = json.loads(rv.data)[f'{name}:history']
    assert len(history) == 4

    # and Alice also has +1
    name = 'Alice'
    rv = client.get(f'/v1/{name}/history')
    assert rv.status_code == 200
    history = json.loads(rv.data)[f'{name}:history']
    assert len(history) == 2


def test_mass_transaction(client):

    # sanity check
    rv = client.get('/v1/Reachy/balance')
    reachy_balance = json.loads(rv.data)['Reachy:balance']
    assert str(reachy_balance) == '15133.21'

    current_reachy_balance = Decimal('15133.21')

    for _ in range(25):
        from_wallet = 'Reachy'
        to_wallet = 'Alice'

        rv = client.put(f'/v1/{from_wallet}/pay?to={to_wallet}&sum=0.01')
        assert rv.status_code == 200

        rv = client.get(f'/v1/{from_wallet}/balance')
        assert rv.status_code == 200
        reachy_balance = json.loads(rv.data)[f'{from_wallet}:balance']
        assert reachy_balance == str(
            current_reachy_balance - Decimal('0.01')
        )
        current_reachy_balance -= Decimal('0.01')

    # Reachy had 15133.21 before, now should have 15132.96 (- 0.25)
    rv = client.get(f'/v1/{from_wallet}/balance')
    assert rv.status_code == 200
    reachy_balance = json.loads(rv.data)[f'{from_wallet}:balance']
    assert reachy_balance == '15132.96'

    # and Alice should posess total 1.26 (+ 0.25)
    rv = client.get(f'/v1/{to_wallet}/balance')
    assert rv.status_code == 200
    alice_balance = json.loads(rv.data)[f'{to_wallet}:balance']
    assert alice_balance == '1.26'
'''
