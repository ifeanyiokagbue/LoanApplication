from enum import unique
from flask import Flask, request, jsonify,make_response
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
import string
import random
from datetime import date, datetime
import requests
#Init app
app = Flask(__name__)

#Database Configration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mutatio:admin900#A@164.92.251.178/mutatio'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Initialise DB 
db = SQLAlchemy(app)

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and auth.username == 'testuser' and auth.password == 'testpassword':
            return f(*args, **kwargs)

        return make_response('Could not verify your login!', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    return decorated


#Loan Application Class
class wallettransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(10))
    amount = db.Column(db.Float)
    transaction_ref = db.Column(db.String(30), unique=True, nullable=False)
    transaction_date = db.Column(db.DateTime)
    status = db.Column(db.String, nullable=False, default='PENDING')

    def __init__(self, transaction_type, amount, transaction_ref, transaction_date):
        self.transaction_type = transaction_type
        self.amount = amount
        self.transaction_ref = transaction_ref
        self.transaction_date = transaction_date


##Routes
@app.route('/wallet/deposit', methods=['POST'])
#@auth_required
def creditWallet():
    transaction_type='CREDIT'
    amount=request.json['amount']
    transaction_date=datetime.now()
    transaction_ref=''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    #if transaction_date >= datetime.today():
    credit_trans = wallettransaction(transaction_type, amount, transaction_ref, transaction_date)
    db.session.add(credit_trans)
    db.session.commit()

        ##persist state to dapr
        #dapr_port = os.getenv("DAPR_HTTP_PORT", 3501)
        #state_url = "http://localhost:{}/v1.0/state/statestore".format(dapr_port)

        #try:
            #response = requests.post(state_url)
            #if not response.ok:
                #return { 'message': response.status_code }

        #except Exception as e:
            #return { 'message':'failed'}

    return jsonify({'message': 'Wallet credited successfully!'})
    # else:
    #     return {'message': 'Date is an older date!'}

@app.route('/wallet/withdraw', methods=['POST'])
#@auth_required
def debitWallet():
    transaction_type= 'DEBIT'
    amount = request.json['amount']
    transaction_date = datetime.now()
    transaction_ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    debit_trans = wallettransaction(transaction_type, amount, transaction_ref, transaction_date)
    
    db.session.add(debit_trans)
    db.session.commit()

    #persist state to dapr
    # dapr_port = os.getenv("DAPR_HTTP_PORT", 3500)
    # state_url = "http://localhost:{}/v1.0/state/statestore".format(dapr_port)

    # try:
    #     response = requests.post(state_url)
    #     if not response.ok:
    #         return { 'message': response.status_code }

    # except Exception as e:
    #     return {'message':'failed'}
    return {'message': 'Wallet withdrawal successful!'}

#Run server
if __name__ == '__main__':
    app.run(debug=True,port=5003,host="0.0.0.0")
