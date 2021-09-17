# Whalet - wallet API service

Simple wallet server. Under construction

![whaletimgs](https://user-images.githubusercontent.com/58036191/132573244-8d56de32-74f1-4d0b-aab0-1672300277d0.png)


# Table of contents

1. [Introduction](#introduction)
2. [Technologies and libraries](#technologies-and-libraries)
3. [API description](#REST-API)
4. [Current development state](#current-development-state)

# Introduction

Whalet is simple wallet application with REST API. Provides basic operations like creating wallet, deposit to wallet and make transactions between wallets. Operation history supported.

Balances stored as Decimal to ensure no troubles with float occured. Given out as string with 2 digits precision.

Service is under construction. Only JSON-rendered responces currently provided, no authorization needed.

# Technologies and libraries

* Python 3.9.5
* Flask/gunicorn
* SQLAlchemy
* marshmallow
* pytest, pylint, flake8, venv

# REST API

#### Create wallet
`create wallet <wallet_name>`

`curl "http://127.0.0.1:5000/v1/create/<wallet_name>" -X POST`

Wallet name restrictions:

- latin letters, numbers and "-" and "_"
- should start with a letter or a number
- 4 <= name length >= 14

#### Response

    201, {"<wallet_name>:created": "true"}

#### Get wallet balance
`get balance for <wallet_name>`

`curl "http://127.0.0.1:5000/v1/<wallet_name>/balance" -X GET`

#### Response

    200, {"<wallet_name>:balance": <actual balance>}

Balance would be a string in 123.00 form (with 2 digits after delimiter).

#### Get list of operations
`get operations history for <wallet_name>`

`curl "http://127.0.0.1:5000/v1/<wallet_name>/history" -X GET`

Only bulk history load currently supported.

#### Response

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

`curl "http://127.0.0.1:5000/v1/<wallet_name>/deposit?sum=<sum>" -X PUT`

**Mandatory arguments:**

| Arg name  |          Description             |
|:---------:|----------------------------------|
| sum       |positive number. If more then 2   |
|           |digits after delimiter passed, the| 
|           |number would be truncated.        | 

#### Response

    200, {"<wallet_name>:new_balance": <actual balance>}

#### Transfer
`transfer some <sum> from <from_wallet_name> to <to_wallet_name>`

`curl "http://127.0.0.1:5000/v1/<from_wallet_name>/pay/?to=<to_wallet_name>&sum=<sum>" -X PUT`

**Mandatory arguments**:

| Arg name      |          Description             |
|:-------------:|----------------------------------|
| sum           |positive number. If more then 2   |
|               |digits after delimiter passed, the| 
|               |number would be truncated.        |
|               |                                  |
|to_wallet_name |name of target wallet where to    |
|               |transfer money to                 |


#### Response

    200, {"<from_wallet_name>:new_balance": <actual balance>}

# Current development state

Project currently is in an early development stage. General functions seemed to work fine as a scratch solution, but state is unstable and some bugs are present for sure.

**Next development steps:**

1) Implemet token-based authorization
2) Pagination for long operation histories
