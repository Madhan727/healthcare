from . import db
from flask_login import UserMixin
from datetime import datetime
import json

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False) # Hashed
    records = db.relationship('PatientRecord', backref='doctor', lazy=True)

class PatientRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_name = db.Column(db.String(100), nullable=True) # Could be self or different
    medicines = db.Column(db.Text, nullable=True) # JSON String
    diseases = db.Column(db.Text, nullable=True) # JSON String
    risk_score = db.Column(db.Float, nullable=True)
    risk_class = db.Column(db.String(20), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "patient_name": self.patient_name,
            "medicines": json.loads(self.medicines) if self.medicines else [],
            "diseases": json.loads(self.diseases) if self.diseases else [],
            "risk_score": self.risk_score,
            "risk_class": self.risk_class,
            "date": self.date_created.isoformat()
        }
