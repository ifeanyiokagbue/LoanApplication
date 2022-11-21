from flask import Flask
from flask_sqlalchemy import SQLAlchemy

#Init app
app = Flask(__name__)

#Database Configration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mutatio:admin900#A@164.92.251.178/mutatio'
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
    
    def __rep__(self):
        return '' & self.ApprovalStatus

def GetLoanApplications():
    db.session.query()

if __name__ == '__main__':
    app.run(debug=True,port=5002)