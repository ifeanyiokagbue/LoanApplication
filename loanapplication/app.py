from enum import unique
import json
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
import uuid
# import json
import requests
from datetime import date, datetime, timedelta
from requests.auth import HTTPBasicAuth

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
class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchantId = db.Column(db.String(100))
    amount = db.Column(db.Float)
    purpose = db.Column(db.Text)
    requestDate = db.Column(db.DateTime)
    paymentDate = db.Column(db.String(10))
    transaction_ref = db.Column(db.String(50))
    ApprovalStatus = db.Column(db.String(10))

    def __init__(self, merchantId, amount, purpose, requestDate, paymentDate,transaction_ref,ApprovalStatus):
        self.merchantId = merchantId
        self.amount = amount
        self.purpose = purpose
        self.requestDate = requestDate
        self.paymentDate = paymentDate
        self.transaction_ref = transaction_ref
        self.ApprovalStatus = ApprovalStatus

##Routes
@app.route('/loans/request', methods=['POST'])
@auth_required
def requestLoan():
    merchantId= request.json['merchantId']
    amount=request.json['amount']
    requestDate= datetime.now()
    purpose = request.json['purpose']
    paymentDate = request.json['paymentDate']
    email = request.json['emailaddress']

    transaction_ref = str(uuid.uuid4())
    ApprovalStatus = 'PENDING'

    #persist data to db
    loan_apply = LoanApplication(merchantId, amount, purpose, requestDate, paymentDate,transaction_ref,ApprovalStatus)
    db.session.add(loan_apply)
    db.session.commit()

    ##invoke the loan processing service
    dapr_port = os.getenv("DAPR_HTTP_PORT", 3501)
    dapr_url = "http://localhost:{}/v1.0/invoke/loanprocessingservice/method/loans/process".format(dapr_port)
    

    message = {
        "merchantId": merchantId,
        "amount": amount, 
        "purpose": purpose, 
        "requestDate": requestDate.strftime("%Y-%m-%d %H:%M:%S"), 
        "paymentDate": paymentDate,
        "transaction_ref": transaction_ref
    }

    try:
        response = requests.post(dapr_url, json=message, timeout=5)
        json_data = response.json()
        approvalStatus = json_data.get('ApprovalStatus')
        loanamount = json_data.get('LoanApprovedAmount')
        if not response.ok:
            return jsonify({'status': 'failed'})
        elif response.ok and approvalStatus == "Rejected":
            ##invoke the credit score service to get the user's credit score
            dapr_port = os.getenv("DAPR_HTTP_PORT", 3505)
            dapr_url = "http://localhost:{}/v1.0/invoke/recommendationservice/method/loanrecommendation".format(dapr_port)
            

            response = requests.get(dapr_url, timeout=5)
            json_data = response.json()
            message = json_data.get('message')
            if not response.ok:
                message = jsonify({'status': 'failed'})
                return make_response(message, 400)
            else:
                message = jsonify({'status': 'failed','ApprovalStatus':'Rejected','Recommendation':str(message)})
                return make_response(message, 400)
    except Exception as e:
        return {'message': e}

    ##Update Loan Application Table
    # result_set = db.execute("Select * from loan_application where merchantId = " + str(merchantId) + " order by Id desc")
    # LoanAppId = result_set('Id')
    # db.execute("update loan_application set ApprovalStatus = 'APPROVED' where merchantId = " + str(merchantId) + " and Id =" + str(LoanAppId))

    ##invoke the wallet service to credit approved amount into the user wallet           
    dapr_port = os.getenv("DAPR_HTTP_PORT", 3503)
    dapr_url = "http://localhost:{}/v1.0/invoke/wallettransactions/method/wallet/deposit".format(dapr_port)
    
    message = {
        "transaction_type": "1",
        "amount": loanamount,
        "transaction_ref": transaction_ref, 
        "transaction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    #return jsonify({'status': 'success', 'message': 'Your loan has been approved and your wallet has been credited.','ApprovalStatus':'Approved'})

    try:
        response = requests.post(dapr_url, json=message, timeout=5)
        json_data = response.json()
        message = json_data.get('message')
        if not response.ok:
            return jsonify({'status': 'failed'})
        elif response.ok and str(message) != "Wallet credited successfully!":
            return jsonify({'status':'success','message':'Your loan has been approved but an error occured while crediting wallet.','ApprovalStatus':'Approved'})
        #return jsonify({'status': 'success', 'message': 'Your loan has been approved and your wallet has been credited.','ApprovalStatus':'Approved'})
    except Exception as e:
        return {'message': e}

    ##invoke the notification service to send notification to the user           
    dapr_port = os.getenv("DAPR_HTTP_PORT", 3506)
    dapr_url = "http://localhost:{}/v1.0/invoke/notificationservice/method/notification/sendemail".format(dapr_port)
    
    message = {
        "toaddress":email,
        "message":"Your loan was approved and your wallet has been credited with the approved loan amount",
        "subject":"Credit Wallet",
        "NotificationType":"Wallet"
    }

    #return jsonify({'status': 'success', 'message': 'Your loan has been approved and your wallet has been credited.','ApprovalStatus':'Approved'})

    try:
        response = requests.post(dapr_url, json=message, timeout=5)
        json_data = response.json()
        message = json_data.get('message')
        if not response.ok:
            return jsonify({'status': 'failed'})
        elif response.ok and str(message) != "success":
            return jsonify({'status':'success','message':'Your loan has been approved and your wallet has been credited but an error occured while sending notification.','ApprovalStatus':'Approved'})
    except Exception as e:
        return {'message': e}
    
    return jsonify({'status': 'success', 'message': 'Your loan has been approved and your wallet has been credited and a notification has been sent to your email.','ApprovalStatus':'Approved'})
#Run server
if __name__ == '__main__':
    app.run(debug=True,port=5002,host="0.0.0.0")
