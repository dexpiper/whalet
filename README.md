# Whalet - wallet API service

Simple wallet server. Under construction

# Table of contents

1. [Introduction](#introduction)
2. [Technologies and libraries](#technologies-and-libraries)
3. [API description](#REST-API)
4. [Current development state](#current-development-state)

# Introduction

Whalet is simple wallet application with REST API. Provides basic operations like creating wallet, deposit to wallet and make transactions between wallets. Also one can get history of operations.
Addition TOKEN-protected method provided to get all current wallets and their balances.

Balances stored as Str and marshalled as Decimal to ensure no troubles with float occured.

Service is under construction. Only JSON-rendered responces currently provided, no authorization needed.

# Technologies and libraries

* Python 3.9.5
* Flask/gunicorn
* SQLAlchemy/flask_sqlalchemy
* marshmallow
* pytest, pylint, flake8, venv

# REST API

#### Create wallet
`create wallet <wallet_name>`

`curl "http://127.0.0.1:5000/v1/create/<wallet_name>" -X POST`

#### Response

    201, {"<wallet_name>:created": "true"}

#### Get wallet balance
`get balance for <wallet_name>`

`curl "http://127.0.0.1:5000/v1/<wallet_name>/balance" -X GET`

#### Response

    200, {"<wallet_name>:balance": <actual balance>}

#### Get list of operations
`get operations history for <wallet_name>`

`curl "http://127.0.0.1:5000/v1/<wallet_name>/history" -X GET`

#### Response

    200, {"<wallet_name>:operations"': [<result>]},
    
    where result - a list of Operations.

    Operation markdown:

    {
        "id"        : a unique identifier of operation
        "get_from"  : wallet from where the transaction came
        "sent_to"   : wallet where the transaction went
        "time"      : date and time in ISO format (like 2021-09-08T10:15:45.856743)
        "optype"    : one of the following types of operation:
                        'creation', 'deposit', 'transaction'
        "amount"    : a number 'ddd.dd', two digits precision. Could be negative in case of outcoming transaction
    }

#### Deposit
`deposit some <sum> to <wallet_name>`

`curl "http://127.0.0.1:5000/v1/<wallet_name>/deposit?sum=<sum>" -X PUT`

Mandatory arguments:

| Arg name  |          Description             |
|:---------:|----------------------------------|
| sum       |positive number. If more then 2   |
|           |digits after delimiter passed, the| 
|           |number would be rounded up or down| 
|           |to 0.01 precision.                |

#### Response

    200, {"<wallet_name>:new_balance": <actual balance>}

#### Transfer
`transfer some <sum> from <from_wallet_name> to <to_wallet_name>`

`curl "http://127.0.0.1:5000/v1/<from_wallet_name>/pay/?to=<to_wallet_name>&sum=<sum>" -X PUT`

Mandatory arguments:

| Arg name      |          Description             |
|:-------------:|----------------------------------|
| sum           |positive number. If more then 2   |
|               |digits after delimiter passed, the| 
|               |number would be rounded up or down| 
|               |to 0.01 precision.                |
|               |                                  |
|to_wallet_name |a name of target wallet where to  |
|               |transfer money into               |





#### Response

    200, {"<from_wallet_name>:new_balance": <actual balance>}

# Current development state

Project currently is in an early development stage. General functions seemed to work fine as a scratch solution, but state is unstable and some bugs are present for sure.

Next development steps:

1) Write tests an improve stability without 500-code error in any quiery
2) Implemet token-based authorization of users
3) Making uuid4-based id for every operation and implement verification mechanism
4) Implement pagination for long operation histories