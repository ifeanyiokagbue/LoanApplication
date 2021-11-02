from enum import unique
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import requests
from datetime import date, datetime

#Init app
app = Flask(__name__)

#Database Configration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:jafar@localhost/mutatioLoanProcessing'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Initialise DB 
db = SQLAlchemy(app)


#Loan Application Class
class LoanProcessing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchantId = db.Column(db.String(100))
    amount = db.Column(db.Float)
    purpose = db.Column(db.Text)
    requestDate = db.Column(db.DateTime)
    paymentDate = db.Column(db.String(10))

    def __init__(self, merchantId, amount, purpose, requestDate, paymentDate):
        self.merchantId = merchantId
        self.amount = amount
        self.purpose = purpose
        self.requestDate = requestDate
        self.paymentDate = paymentDate


##Routes
@app.route('/loans/process', methods=['POST'])
def processLoan():
    merchantId= request.json['merchantId']
    amount=request.json['amount']
    requestDate= request.json['requestDate']
    purpose = request.json['purpose']
    paymentDate = request.json['paymentDate']

    loan_process = LoanProcessing(merchantId, amount, purpose, requestDate, paymentDate)
    db.session.add(loan_process)
    db.session.commit()

    return {'message': 'success'}

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
    app.run(debug=True)
