from enum import unique
import json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
# import json
import requests
from datetime import date, datetime

#Init app
app = Flask(__name__)

#Database Configration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:jafar@localhost/mutatioLoanApplication'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Initialise DB 
db = SQLAlchemy(app)


#Loan Application Class
class LoanApplication(db.Model):
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
@app.route('/loans/request', methods=['POST'])
def requestLoan():
    merchantId= request.json['merchantId']
    amount=request.json['amount']
    requestDate= datetime.now()
    purpose = request.json['purpose']
    paymentDate = request.json['paymentDate']

    #persist data to db
    loan_apply = LoanApplication(merchantId, amount, purpose, requestDate, paymentDate)
    db.session.add(loan_apply)
    db.session.commit()

    ##invoke the loan processing service
    dapr_port = os.getenv("DAPR_HTTP_PORT", 3500)
    dapr_url = "http://localhost:{}/v1.0/invoke/loanprocessingservice/method/loans/process".format(dapr_port)
    

    message = {
        "merchantId": merchantId,
        "amount": amount, 
        "purpose": purpose, 
        "requestDate": requestDate.strftime("%Y-%m-%d %H:%M:%S"), 
        "paymentDate": paymentDate
    }

    try:
        response = requests.post(dapr_url, json=message, timeout=5)
        if not response.ok:
            return jsonify({'status': 'failed'})
    except Exception as e:
        return {'message': e}

    return jsonify({'status': 'success', 'message': 'Your loan has been approved'})

#Run server
if __name__ == '__main__':
    app.run(debug=True)
