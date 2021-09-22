# Whalet - wallet API service

Simple wallet server.

![whaletimgs](https://user-images.githubusercontent.com/58036191/132573244-8d56de32-74f1-4d0b-aab0-1672300277d0.png)


# Table of contents

1. [Introduction](#introduction)
2. [Technologies and libraries](#technologies-and-libraries)
3. [API description](#REST-API)
4. [Current development state](#current-development-state)

# Introduction

Whalet is simple wallet application with REST API. Provides basic operations like creating wallet, deposit to wallet and make transactions between wallets. Operation history supported.

Balances stored as Decimal to ensure no troubles with float occurred. Given out as string with 2 digits precision.

Service is under construction. Only JSON-rendered responses currently provided.

# Technologies and libraries

* Python 3.9.5
* Flask/gunicorn
* Flask-HTTPAuth
* SQLAlchemy
* marshmallow
* pytest, pylint, flake8, venv

# REST API

#### Create wallet
`create wallet <wallet_name> with <password>`

`curl "http://127.0.0.1:5000/v1/create?name=<wallet_name>&pwd=<password>" -X POST`

Wallet name restrictions:

- Latin letters, numbers and "-" and "_"
- should start with a letter or a number
- 4 <= name length >= 14

Password restrictions:
- Latin letters, numbers and -_$%:#@*!><.,~ symbols
- should start with a letter or a number
- 6 <= pass length >= 14


---> Response:

    201, {"<wallet_name>:created": "true"}

#### Get wallet balance
`get balance for <wallet_name>`

`curl -u '<wallet_name>:<password>' "http://127.0.0.1:5000/v1/balance" -X GET`

---> Response:

    200, {"<wallet_name>:balance": <actual balance>}

Balance would be a string in 123.00 form (with 2 digits after delimiter).

#### Get list of operations
`get operations history for <wallet_name>`

`curl -u '<wallet_name>:<password>' "http://127.0.0.1:5000/v1/history" -X GET`

Only bulk history load currently supported.

---> Response:

    200, {"<wallet_name>:operations"': [<result>]},
    
    where result - a list of Operations.

    Operation markdown:

    {
        "id"        : a unique identifier of operation (UUID4)
        "get_from"  : wallet from where the transaction came
        "sent_to"   : wallet where the transaction went
        "time"      : date and time in ISO format (like 2021-09-08T10:15:45.856743)
        "optype"    : one of the following types of operation:
                        'creation', 'deposit', 'transaction'
        "amount"    : a number 'ddd.dd', two digits precision. 
                        Could be negative in case of outcoming transaction
    }

#### Deposit
`deposit some <sum> to <wallet_name>`

`curl "http://127.0.0.1:5000/v1/deposit?to=<wallet_name>&sum=<sum>&token=<MASTER_TOKEN>" -X PUT`

**Mandatory arguments:**

| Arg name    |          Description             |
|:-----------:|----------------------------------|
| sum         |positive number. If more then 2   |
|             |digits after delimiter passed, the| 
|             |number would be truncated.        | 
| wallet_name | name of target wallet            |
| token       |application master token          |

---> Response:

    200, {"<wallet_name>:new_balance": <actual balance>}

#### Transfer
`transfer some <sum> from <from_wallet_name> to <to_wallet_name>`

`curl -u <from_wallet_name>:<password> "http://127.0.0.1:5000/v1/pay/?to=<to_wallet_name>&sum=<sum>" -X PUT`

**Mandatory arguments**:

| Arg name      |          Description             |
|:-------------:|----------------------------------|
| sum           |positive number. If more then 2   |
|               |digits after delimiter passed, the| 
|               |number would be truncated.        |
|               |                                  |
|to_wallet_name |name of target wallet where to    |
|               |transfer money to                 |


---> Response:

    200, {"<from_wallet_name>:new_balance": <actual balance>}

# Current development state

Project currently is under construction. General functions seemed to work fine as a scratch solution, but state is unstable and some bugs are present for sure.

**Next development steps:**

1) Pagination for long operation histories
2) Session protection and other improvements for more stable work under load
3) Security improvements
