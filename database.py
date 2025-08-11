import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from dotenv import load_dotenv
import random

# Load environment variables from .env file (for local development)
load_dotenv()

app = Flask(__name__)
# Get the database URL from an environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")

if not app.config['SQLALCHEMY_DATABASE_URI']:
    raise ValueError("No DATABASE_URL set. Please set it in your environment variables.")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:123@localhost/Healthcare_Mgt'
db = SQLAlchemy(app)


class Patients(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    pat_ref = db.Column(db.String(7), unique=True, nullable=False, index=True,
                        default=lambda: f"PT-{random.randint(1000, 9999)}")
    blood_group = db.Column(db.String(20))
    patient_phone = db.Column(db.String(11), unique=True, nullable=False, index=True)
    next_of_kin = db.Column(db.String(100), nullable=False)
    presenting_complaint = db.Column(db.Text, nullable=False)
    admission_date = db.Column(db.Date, nullable=False)
    visits = db.relationship('Visits', backref='patients', lazy=True)

    def __init__(self, **kwargs):
        super(Patients, self).__init__(**kwargs)
        # Ensure uniqueness by regenerating if needed
        while db.session.query(Patients).filter_by(pat_ref=self.pat_ref).first() is not None:
            self.pat_ref = f"PT-{random.randint(1000, 9999)}"


class Visits(db.Model):
    __tablename__ = 'visits'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    tests = db.Column(db.Text)
    medication = db.Column(db.Text)
    next_appointment = db.Column(db.Date)
    attending_physician = db.Column(db.String(100), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))


class Doctors(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    staff_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(100))
    password = db.Column(db.String(255), nullable=False)


class PatientLogin(db.Model):
    __tablename__ = 'patient_login'

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(11), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print('Tables Successfully Created')




