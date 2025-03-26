# This file will be used in the future for database models
# For now, we're using mock data stored in app.py

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User preferences
    preferred_destinations = db.Column(db.String(200))
    accommodation_type = db.Column(db.String(50))
    budget = db.Column(db.String(20))
    
    # Relationships
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade="all, delete-orphan")
    travel_plans = db.relationship('TravelPlan', backref='user', lazy=True, cascade="all, delete-orphan")
    price_monitors = db.relationship('PriceMonitor', backref='user', lazy=True, cascade="all, delete-orphan")
    
    # Métodos necessários para Flask-Login
    def is_authenticated(self):
        return True
        
    def is_active(self):
        return True
        
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return str(self.id)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade="all, delete-orphan", order_by="Message.timestamp")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'))
    is_user = db.Column(db.Boolean, default=True)  # True if user message, False if assistant
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class TravelPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200))
    destination = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    flights = db.relationship('Flight', backref='travel_plan', lazy=True, cascade="all, delete-orphan")
    accommodations = db.relationship('Accommodation', backref='travel_plan', lazy=True, cascade="all, delete-orphan")

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
    currency = db.Column(db.String(3), default='BRL')
    booking_link = db.Column(db.String(500))
    
    # Para armazenar os dados completos da oferta
    offer_data = db.Column(JSON, nullable=True)

class Accommodation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    travel_plan_id = db.Column(db.Integer, db.ForeignKey('travel_plan.id'))
    name = db.Column(db.String(200))
    location = db.Column(db.String(200))
    check_in = db.Column(db.Date)
    check_out = db.Column(db.Date)
    price_per_night = db.Column(db.Float)
    currency = db.Column(db.String(3), default='BRL')
    stars = db.Column(db.Integer)
    booking_link = db.Column(db.String(500))
    
    # Para armazenar os dados completos da oferta
    offer_data = db.Column(JSON, nullable=True)

# Sistema de monitoramento de preços
class PriceMonitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.String(10))  # 'flight' ou 'hotel'
    
    # Identificadores e detalhes
    item_id = db.Column(db.String(100)) # ID do item na API externa (voo ou hotel)
    name = db.Column(db.String(200))    # Nome amigável (companhia aérea + número do voo, ou nome do hotel)
    description = db.Column(db.String(500)) # Descrição (origem-destino, ou localização do hotel)
    
    # Informações de preço
    original_price = db.Column(db.Float)
    current_price = db.Column(db.Float)
    lowest_price = db.Column(db.Float)
    currency = db.Column(db.String(3), default='BRL')
    
    # Datas
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    last_checked = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Dados completos para rechecagem
    offer_data = db.Column(JSON)
    
    # Relacionamento
    price_history = db.relationship('PriceHistory', backref='monitor', lazy=True, cascade="all, delete-orphan")
    price_alerts = db.relationship('PriceAlert', backref='monitor', lazy=True, cascade="all, delete-orphan")

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey('price_monitor.id'))
    price = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class PriceAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey('price_monitor.id'))
    old_price = db.Column(db.Float)
    new_price = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    preferred_destinations = db.Column(db.String(200))
    accommodation_type = db.Column(db.String(50))
    budget = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade="all, delete-orphan")
    travel_plans = db.relationship('TravelPlan', backref='user', lazy=True, cascade="all, delete-orphan")
    price_monitors = db.relationship('PriceMonitor', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade="all, delete-orphan")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    is_user = db.Column(db.Boolean, default=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class TravelPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    flights = db.relationship('Flight', backref='travel_plan', lazy=True, cascade="all, delete-orphan")
    accommodations = db.relationship('Accommodation', backref='travel_plan', lazy=True, cascade="all, delete-orphan")

class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    travel_plan_id = db.Column(db.Integer, db.ForeignKey('travel_plan.id'), nullable=False)
    airline = db.Column(db.String(100))
    flight_number = db.Column(db.String(20))
    departure_location = db.Column(db.String(200))
    arrival_location = db.Column(db.String(200))
    departure_time = db.Column(db.DateTime)
    arrival_time = db.Column(db.DateTime)
    price = db.Column(db.Float)
    currency = db.Column(db.String(3))

class Accommodation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    travel_plan_id = db.Column(db.Integer, db.ForeignKey('travel_plan.id'), nullable=False)
    name = db.Column(db.String(200))
    location = db.Column(db.String(200))
    check_in = db.Column(db.Date)
    check_out = db.Column(db.Date)
    price_per_night = db.Column(db.Float)
    currency = db.Column(db.String(3))
    stars = db.Column(db.Integer)

class PriceMonitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'flight' ou 'hotel'
    item_id = db.Column(db.String(100))
    name = db.Column(db.String(200))
    description = db.Column(db.String(200))
    original_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    lowest_price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    last_checked = db.Column(db.DateTime, default=datetime.utcnow)
    offer_data = db.Column(db.JSON)
    
    # Relacionamentos
    price_history = db.relationship('PriceHistory', backref='monitor', lazy=True, cascade="all, delete-orphan")
    alerts = db.relationship('PriceAlert', backref='monitor', lazy=True, cascade="all, delete-orphan")

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey('price_monitor.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class PriceAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey('price_monitor.id'), nullable=False)
    old_price = db.Column(db.Float, nullable=False)
    new_price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
