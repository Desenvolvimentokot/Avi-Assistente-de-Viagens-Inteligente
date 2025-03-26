# This file will be used in the future for database models
# For now, we're using mock data stored in app.py

'''
Example model structure for future implementation:

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(256))
    
    # User preferences
    preferred_destinations = db.Column(db.String(200))
    accommodation_type = db.Column(db.String(50))
    budget = db.Column(db.String(20))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200))
    last_updated = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    messages = db.relationship('Message', backref='conversation', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'))
    is_user = db.Column(db.Boolean, default=True)  # True if user message, False if assistant
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class TravelPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200))
    destination = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    details = db.Column(db.Text)
    
    # Additional details for travel plans
    flights = db.relationship('Flight', backref='travel_plan', lazy=True)
    accommodations = db.relationship('Accommodation', backref='travel_plan', lazy=True)

class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    travel_plan_id = db.Column(db.Integer, db.ForeignKey('travel_plan.id'))
    airline = db.Column(db.String(100))
    flight_number = db.Column(db.String(20))
    departure_location = db.Column(db.String(200))
    arrival_location = db.Column(db.String(200))
    departure_time = db.Column(db.DateTime)
    arrival_time = db.Column(db.DateTime)
    price = db.Column(db.Float)

class Accommodation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    travel_plan_id = db.Column(db.Integer, db.ForeignKey('travel_plan.id'))
    name = db.Column(db.String(200))
    location = db.Column(db.String(200))
    check_in = db.Column(db.Date)
    check_out = db.Column(db.Date)
    price_per_night = db.Column(db.Float)
    stars = db.Column(db.Integer)
'''
