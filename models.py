from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    conversations = db.relationship('Conversation', backref='user', lazy=True)
    travel_plans = db.relationship('TravelPlan', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Conversation {self.title}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Message {self.id}>'

class TravelPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    budget = db.Column(db.Float)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    price_monitors = db.relationship('PriceMonitor', backref='travel_plan', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<TravelPlan {self.title}>'

class PriceMonitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    travel_plan_id = db.Column(db.Integer, db.ForeignKey('travel_plan.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'flight' ou 'hotel'
    origin = db.Column(db.String(3))  # Código IATA para voos
    destination = db.Column(db.String(3))  # Código IATA para voos ou cidade para hotéis
    departure_date = db.Column(db.Date)
    return_date = db.Column(db.Date)
    offer_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)

    price_history = db.relationship('PriceHistory', backref='price_monitor', lazy=True, cascade='all, delete-orphan')
    price_alerts = db.relationship('PriceAlert', backref='price_monitor', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PriceMonitor {self.id}>'

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price_monitor_id = db.Column(db.Integer, db.ForeignKey('price_monitor.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='BRL')
    timestamp = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PriceHistory {self.id}>'

class PriceAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price_monitor_id = db.Column(db.Integer, db.ForeignKey('price_monitor.id'), nullable=False)
    target_price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_triggered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    triggered_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<PriceAlert {self.id}>'