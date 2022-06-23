from flask import Flask, g, jsonify, request
from uuid import uuid4
from time import strftime
import sqlite3
import os
import binascii

app = Flask(__name__)

DATABASE = './database.db'

# START DATABASE RELATED METHODS #
def dictFactory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def getDb():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = dictFactory
    return db

@app.teardown_appcontext
def closeConnection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
# END DATABASE RELATED METHODS #

# START UTILS METHODS #
def accountExists(accountId):
    cur = getDb().cursor()
    cur.execute("SELECT * FROM accounts WHERE id = ?", (accountId,))
    rows = cur.fetchall()
    return len(rows) == 1

def computeAccountBalance(accountId):
    balance = 0.0
    cur = getDb().cursor()
    cur.execute("SELECT * FROM transactions WHERE account_from = ? OR account_to = ?", (accountId, accountId))
    rows = cur.fetchall()
    for row in rows:
        if row['type'] == 'transfer':
            # if type is a transfer, add the amount to the balance if the current account is the receiver, otherwise subtract it
            balance += row['amount'] * (1 if row['account_to'] == accountId else -1)
        else:
            # if type is a deposit, add the amount to the balance, else if type is a withdrawal, subtract it
            balance += row['amount'] * (1 if row['type'] == "deposit" else -1)
    return balance

def performTransferImpl(fromAccount, toAccount, amount):
    if not accountExists(fromAccount):
        return {
            'error': "L'account del mittente non esiste"
        }, 404

    if not accountExists(toAccount):
        return {
            'error': "L'account del destinatario non esiste"
        }, 404

    if (amount <= 0):
        return {
            'error': "L'importo della transazione deve essere positivo",
        }, 400

    if computeAccountBalance(fromAccount) < amount:
        return {
            'error': "Il saldo non è sufficiente per effettuare l'operazione richiesta"
        }, 422

    transactionId = str(uuid4())
    createdAt = strftime("%Y-%m-%d %H:%M:%S")
    cur = getDb().cursor()
    cur.execute(
        "INSERT INTO transactions (id, account_from, account_to, type, amount, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (transactionId, fromAccount, toAccount, "transfer", amount, createdAt)
    )
    getDb().commit()

    return {
        'id': transactionId,
        'balances': {
            fromAccount: computeAccountBalance(fromAccount),
            toAccount: computeAccountBalance(toAccount)
        }
    }
# END UTILS METHODS

# START ROUTES METHODS
@app.route("/api/account", methods=['GET'])
def getAccountsList():
    cur = getDb().cursor()
    cur.execute("SELECT * FROM accounts")
    rows = cur.fetchall()
    return jsonify(rows)

@app.route("/api/account", methods=['POST'])
def createAccount():
    id = binascii.b2a_hex(os.urandom(10)).decode('ascii')
    cur = getDb().cursor()
    cur.execute("INSERT INTO accounts (id, name, surname) VALUES (?, ?, ?)", (id, request.json['name'], request.json['surname']))
    getDb().commit()
    return { 'id': id }

@app.route("/api/account/", methods=['DELETE'])
def deleteAccount():
    accountId = request.args['id']

    if not accountExists(accountId):
        return {
            'error': "Non esiste un account con l'id specificato"
        }, 404

    cur = getDb().cursor()
    cur.execute("DELETE FROM accounts WHERE id = ?", (accountId,))
    getDb().commit()
    return ("", 204)

@app.route("/api/account/<accountId>", methods=['GET'])
def getAccount(accountId):
    if not accountExists(accountId):
        return {
            'error': "Non esiste un account con l'id specificato"
        }, 404

    cur = getDb().cursor()
    cur.execute("SELECT name, surname FROM accounts WHERE id = ?", (accountId,))
    account = cur.fetchone()

    # select all the transaction fields if "detailed" URL param is set, or only the id otherwise
    cur.execute("SELECT " + ('*' if 'detailed' in request.args else 'id') + " FROM transactions WHERE account_from = ? ORDER BY created_at", (accountId,))
    transactions = cur.fetchall()

    response = account | {
        'balance': computeAccountBalance(accountId),
        'transactions': transactions
    }

    headers = { "X-Sistema-Bancario": account['name'] + ';' + account['surname']}

    return response, headers

@app.route("/api/account/<accountId>", methods=['POST'])
def performDeposit(accountId):
    cur = getDb().cursor()
    id = str(uuid4())
    createdAt = strftime("%Y-%m-%d %H:%M:%S")
    amount = float(request.json['amount'])
    type = "deposit" if amount >= 0 else "withdrawal"
    amount = abs(amount)

    # check if the account exists
    if not accountExists(accountId):
        return {
            'error': "Non esiste un account con l'id specificato"
        }, 404

    # check if the balance is enough
    balance = computeAccountBalance(accountId)
    if (amount > balance and type == "withdrawal"):
        return {
            'error': "Il saldo non è sufficiente per effettuare il prelievo richiesto"
        }, 422

    cur = getDb().cursor()
    cur.execute(
        "INSERT INTO transactions (id, account_from, type, amount, created_at) VALUES (?, ?, ?, ?, ?)",
        (id, accountId, type, amount, createdAt)
    )
    getDb().commit()

    return {
        'id': id,
        'balance': computeAccountBalance(accountId)
    }

@app.route("/api/account/<accountId>", methods=['PUT'])
def updateAccountDetails(accountId):
    if not accountExists(accountId):
        return {
            'error': "Non esiste un account con l'id specificato"
        }, 404

    cur = getDb().cursor()
    cur.execute("UPDATE accounts SET name = ?, surname = ? WHERE id = ?", (request.json['name'], request.json['surname'], accountId))
    getDb().commit()
    return "", 204

@app.route("/api/account/<accountId>", methods=['PATCH'])
def updateAccountSingleDetail(accountId):
    if not accountExists(accountId):
        return {
            'error': "Non esiste un account con l'id specificato"
        }, 404

    cur = getDb().cursor()

    if "name" in request.json:
        cur.execute("UPDATE accounts SET name = ? WHERE id = ?", (request.json['name'], accountId))
    elif "surname" in request.json:
        cur.execute("UPDATE accounts SET surname = ? WHERE id = ?", (request.json['surname'], accountId))
    else:
        return {
            'error': "È necessario specificare il campo 'name' o 'surname'"
        }, 400

    getDb().commit()
    return "", 204

@app.route("/api/account/<accountId>", methods=['HEAD'])
def getAccountHeader():
    cur = getDb().cursor()
    cur.execute("SELECT * FROM accounts WHERE id = ?", (accountId,))
    rows = cur.fetchall()

    if len(rows) != 1:
        return {
            'error': "Non esiste un account con l'id specificato"
        }, 404

    account = rows[0]

    return "", 204, { "X-Sistema-Bancario": account['name'] + ';' + account['surname']}

@app.route("/api/transfer/", methods=['POST'])
def performTransfer():
    fromAccount = request.json['from']
    toAccount = request.json['to']
    amount = float(request.json['amount'])

    return performTransferImpl(fromAccount, toAccount, amount)

@app.route("/api/divert", methods=['POST'])
def divertTransfer():
    cur = getDb().cursor()
    cur.execute("SELECT * FROM transactions WHERE id = ?", (request.json['id'],))
    row = cur.fetchone()

    if not row:
        return {
            'error': "La transazione con id specificato non esiste"
        }, 404

    return performTransferImpl(row['account_to'], row['account_from'], row['amount'])
# END ROUTES METHODS
