
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Preferências do usuário
    phone = db.Column(db.String(20), nullable=True)
    preferred_destinations = db.Column(db.String(255), nullable=True)
    accommodation_type = db.Column(db.String(50), nullable=True)
    budget = db.Column(db.Float, nullable=True)

    conversations = db.relationship('Conversation', backref='user', lazy=True)
    travel_plans = db.relationship('TravelPlan', backref='user', lazy=True)
    price_monitors = db.relationship('PriceMonitor', backref='user', lazy=True)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.name}>'

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

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
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    flights = db.relationship('FlightBooking', backref='travel_plan', lazy=True, cascade='all, delete-orphan')
    accommodations = db.relationship('Accommodation', backref='travel_plan', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<TravelPlan {self.title}>'

class FlightBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    travel_plan_id = db.Column(db.Integer, db.ForeignKey('travel_plan.id'), nullable=False)
    airline = db.Column(db.String(50))
    flight_number = db.Column(db.String(20))
    departure_location = db.Column(db.String(50))
    arrival_location = db.Column(db.String(50))
    departure_time = db.Column(db.DateTime)
    arrival_time = db.Column(db.DateTime)
    price = db.Column(db.Float)
    currency = db.Column(db.String(3), default="BRL")
    booking_status = db.Column(db.String(20), default="planned")  # planned, booked, confirmed, cancelled

class Accommodation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    travel_plan_id = db.Column(db.Integer, db.ForeignKey('travel_plan.id'), nullable=False)
    name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    check_in = db.Column(db.Date)
    check_out = db.Column(db.Date)
    price_per_night = db.Column(db.Float)
    currency = db.Column(db.String(3), default="BRL")
    stars = db.Column(db.Integer)
    booking_status = db.Column(db.String(20), default="planned")  # planned, booked, confirmed, cancelled

class PriceMonitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'flight' ou 'hotel'
    item_id = db.Column(db.String(100))  # ID da oferta original
    name = db.Column(db.String(100))  # Nome do voo ou hotel
    description = db.Column(db.String(255))  # Descrição (rota, localização)
    original_price = db.Column(db.Float, nullable=False)  # Preço original
    current_price = db.Column(db.Float, nullable=False)  # Preço atual
    lowest_price = db.Column(db.Float, nullable=False)  # Menor preço registrado
    currency = db.Column(db.String(3), default='BRL')
    date_added = db.Column(db.DateTime, default=datetime.now)
    last_checked = db.Column(db.DateTime, default=datetime.now)
    offer_data = db.Column(db.JSON)  # Dados completos da oferta

    price_history = db.relationship('PriceHistory', backref='monitor', lazy=True, cascade='all, delete-orphan')
    price_alerts = db.relationship('PriceAlert', backref='monitor', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PriceMonitor {self.id} - {self.type}>'

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey('price_monitor.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PriceHistory {self.id}>'

class PriceAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey('price_monitor.id'), nullable=False)
    old_price = db.Column(db.Float, nullable=False)
    new_price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<PriceAlert {self.id}>'
