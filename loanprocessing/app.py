#from enum import unique
from flask import Flask, request, jsonify,make_response
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
import requests
from datetime import date, datetime

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
class LoanProcessing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchantId = db.Column(db.String(100))
    amount = db.Column(db.Float)
    purpose = db.Column(db.Text)
    requestDate = db.Column(db.DateTime)
    paymentDate = db.Column(db.String(10))
    transaction_ref = db.Column(db.String(50))

    def __init__(self, merchantId, amount, purpose, requestDate, paymentDate,transaction_ref):
        self.merchantId = merchantId
        self.amount = amount
        self.purpose = purpose
        self.requestDate = requestDate
        self.paymentDate = paymentDate
        self.transaction_ref = transaction_ref


##Routes
@app.route('/loans/process', methods=['POST'])
#@auth_required
def processLoan():
    merchantId= request.json['merchantId']
    amount=request.json['amount']
    requestDate= request.json['requestDate']
    purpose = request.json['purpose']
    paymentDate = request.json['paymentDate']
    transaction_ref = request.json['transaction_ref']

    ##invoke the credit score service to get the user's credit score
    dapr_port = os.getenv("DAPR_HTTP_PORT", 3504)
    dapr_url = "http://localhost:{}/v1.0/invoke/creditscoreservice/method/creditscore/getusercreditscore".format(dapr_port)
    

    message = {
        "userId": 5,
    }

    try:
        response = requests.get(dapr_url, json=message, timeout=5)
        json_data = response.json()
        creditscore = json_data.get('message')
        if not response.ok:
            return jsonify({'status': 'failed','ApprovalStatus':'Rejected','LoanApprovedAmount':0.00})
        elif response.ok and 'message' in json_data and creditscore < 5:
            return jsonify({'message':'Loan was rejected because you had a low credit score of: ' + str(creditscore),'ApprovalStatus':'Rejected','LoanApprovedAmount':0.00})
            #return jsonify({'message':'Loan not processed because you had low credit score.'})
    except Exception as e:
        return {'message': e}

    loan_process = LoanProcessing(merchantId, amount, purpose, requestDate, paymentDate,transaction_ref)
    db.session.add(loan_process)
    db.session.commit()

    loanamount = int(amount) + 0.00
    return {'status': 'success','message':'Your Loan has been approved','Credit Score':creditscore,'ApprovalStatus':'Approved','LoanApprovedAmount':loanamount}

    # ##persist state to dapr
    # dapr_port = os.getenv("DAPR_HTTP_PORT", 3500)
    # state_url = "http://localhost:{}/v1.0/state/statestore".format(dapr_port)
    # dapr_state = {}
    # try:
    #     response = requests.post(state_url, data={'key': 'value'})
    #     if not response.ok:
    #         return { 'message': 'failed', 'body': {response.status_code,  response.content.decode("utf-8")}}

    # except Exception as e:
    #     return { 'message':'failed', 'body': e}
#Run server
if __name__ == '__main__':
    app.run(debug=True,port=5001,host="0.0.0.0")
