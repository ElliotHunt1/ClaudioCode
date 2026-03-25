from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

DATA_DIR = 'data'
SQLITE_PATH = os.path.join(DATA_DIR, 'app.db')
BOOKINGS_FILE = os.path.join(DATA_DIR, 'bookings.json')
ITINERARY_FILE = os.path.join(DATA_DIR, 'itinerary.json')

os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = os.getenv('RAILWAY_DATABASE_URL') or os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
if not DATABASE_URL:
    DATABASE_URL = f'sqlite:///{SQLITE_PATH}'

engine_kwargs = {}
if DATABASE_URL.startswith('sqlite'):
    engine_kwargs['connect_args'] = {'check_same_thread': False}

engine = create_engine(DATABASE_URL, echo=False, future=True, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    date = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    notes = Column(Text, default='')
    cost = Column(Float, default=0.0)
    currency = Column(String(10), default='AUD')

class ItineraryDay(Base):
    __tablename__ = 'itinerary_days'
    id = Column(Integer, primary_key=True, autoincrement=True)
    day = Column(Integer, nullable=False, unique=True)
    date = Column(String(50), default='')
    locations = Column(JSON, default=list)
    activities = Column(JSON, default=list)
    notes = Column(Text, default='')

def get_db_session():
    return SessionLocal()

def init_db():
    Base.metadata.create_all(bind=engine)

def booking_to_dict(b):
    return {
        'id': b.id,
        'title': b.title,
        'date': b.date,
        'location': b.location,
        'notes': b.notes,
        'cost': b.cost,
        'currency': b.currency,
    }

def itinerary_day_to_dict(d):
    return {
        'id': d.id,
        'day': d.day,
        'date': d.date,
        'locations': d.locations or [],
        'activities': d.activities or [],
        'notes': d.notes or '',
    }

# JSON fallback for local debugging (not persistent on Railway)

def load_bookings():
    try:
        with get_db_session() as db:
            rows = db.query(Booking).order_by(Booking.id).all()
            return [booking_to_dict(r) for r in rows]
    except Exception:
        if os.path.exists(BOOKINGS_FILE):
            with open(BOOKINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

def save_bookings(bookings):
    try:
        with get_db_session() as db:
            db.query(Booking).delete()
            db.commit()
            for item in bookings:
                b = Booking(
                    title=item.get('title', 'Untitled'),
                    date=item.get('date', ''),
                    location=item.get('location', ''),
                    notes=item.get('notes', ''),
                    cost=float(item.get('cost', 0.0) or 0.0),
                    currency=item.get('currency', 'AUD')
                )
                db.add(b)
            db.commit()
    except Exception:
        with open(BOOKINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(bookings, f, indent=2)

def load_itinerary():
    try:
        with get_db_session() as db:
            rows = db.query(ItineraryDay).order_by(ItineraryDay.day).all()
            if rows:
                return [itinerary_day_to_dict(r) for r in rows]
            # seed 21 days if empty
            itinerary = []
            for i in range(21):
                day = ItineraryDay(day=i+1, date='', locations=[], activities=[], notes='')
                db.add(day)
                itinerary.append(day)
            db.commit()
            return [itinerary_day_to_dict(d) for d in itinerary]
    except Exception:
        if os.path.exists(ITINERARY_FILE):
            with open(ITINERARY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return [{'day': i+1, 'date': '', 'locations': [], 'activities': [], 'notes': ''} for i in range(21)]

def save_itinerary(itinerary):
    try:
        with get_db_session() as db:
            for item in itinerary:
                day_index = int(item.get('day', 0))
                if day_index < 1:
                    continue
                existing = db.query(ItineraryDay).filter_by(day=day_index).first()
                if existing:
                    existing.date = item.get('date', '')
                    existing.locations = item.get('locations', []) or []
                    existing.activities = item.get('activities', []) or []
                    existing.notes = item.get('notes', '')
                else:
                    new_day = ItineraryDay(
                        day=day_index,
                        date=item.get('date', ''),
                        locations=item.get('locations', []) or [],
                        activities=item.get('activities', []) or [],
                        notes=item.get('notes', '')
                    )
                    db.add(new_day)
            db.commit()
    except Exception:
        with open(ITINERARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(itinerary, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/budget')
def budget():
    return render_template('budget.html')

@app.route('/itinerary')
def itinerary():
    itinerary_data = load_itinerary()
    return render_template('itinerary.html', itinerary=itinerary_data)

@app.route('/bookings')
def bookings():
    bookings_data = load_bookings()
    return render_template('bookings.html', bookings=bookings_data)

CURRENCY_RATES = {
    'AUD': 1.0,
    'USD': 0.67,
    'EUR': 0.60,
    'GBP': 0.52
}

def safe_float(value):
    try:
        if value is None or value == '':
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def get_live_rates(base='AUD'):
    import requests
    try:
        resp = requests.get(f'https://api.exchangerate.host/latest?base={base}&symbols=USD,EUR,GBP,AUD', timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if 'rates' in data:
            return data['rates']
    except Exception:
        pass
    return None

@app.route('/api/budget/calculate', methods=['POST'])
def calculate_budget():
    data = request.json or {}
    currency = data.get('currency', 'AUD').upper()
    if currency not in CURRENCY_RATES:
        currency = 'AUD'

    flights = safe_float(data.get('flights', 0))
    accommodation = safe_float(data.get('accommodation', 0))
    food = safe_float(data.get('food', 0))
    activities = safe_float(data.get('activities', 0))
    transport = safe_float(data.get('transport', 0))
    misc = safe_float(data.get('misc', 0))

    subtotal = flights + accommodation + food + activities + transport + misc
    contingency = subtotal * 0.1
    total = subtotal + contingency

    rates = get_live_rates(base='AUD')
    if rates and currency in rates:
        rate = rates[currency]
    else:
        rate = CURRENCY_RATES.get(currency, 1.0)

    total_aud = round(total / rate, 2)
    subtotal_aud = round(subtotal / rate, 2)
    contingency_aud = round(contingency / rate, 2)

    return jsonify({
        'subtotal': round(subtotal, 2),
        'contingency': round(contingency, 2),
        'total': round(total, 2),
        'currency': currency,
        'rate': rate,
        'subtotal_aud': subtotal_aud,
        'contingency_aud': contingency_aud,
        'total_aud': total_aud,
        'live_rates': rates or CURRENCY_RATES
    })

@app.route('/api/itinerary/update', methods=['POST'])
def update_itinerary():
    data = request.json or {}
    if 'day' not in data:
        return jsonify({'error': 'day is required'}), 400

    day_index = int(data['day'])
    itinerary = load_itinerary()
    if 1 <= day_index <= len(itinerary):
        itinerary[day_index-1] = {
            'id': itinerary[day_index-1].get('id'),
            'day': day_index,
            'date': data.get('date', ''),
            'locations': data.get('locations', []),
            'activities': data.get('activities', []),
            'notes': data.get('notes', '')
        }
        save_itinerary(itinerary)
        return jsonify({'success': True})

    return jsonify({'error': 'Invalid day'}), 400

@app.route('/api/bookings', methods=['GET', 'POST'])
def handle_bookings():
    if request.method == 'GET':
        return jsonify(load_bookings())

    data = request.json or {}
    bookings = load_bookings()

    if 'id' in data and data.get('id') is not None:
        updated = False
        for i, booking in enumerate(bookings):
            if booking['id'] == int(data['id']):
                booking.update({
                    'title': data.get('title', booking.get('title', 'Untitled')),
                    'date': data.get('date', booking.get('date', '')),
                    'location': data.get('location', booking.get('location', '')),
                    'notes': data.get('notes', booking.get('notes', '')),
                    'cost': float(data.get('cost', booking.get('cost', 0.0)) or 0.0),
                    'currency': data.get('currency', booking.get('currency', 'AUD'))
                })
                updated = True
                break
        if not updated:
            bookings.append({
                'id': int(data.get('id')),
                'title': data.get('title', 'Untitled'),
                'date': data.get('date', ''),
                'location': data.get('location', ''),
                'notes': data.get('notes', ''),
                'cost': float(data.get('cost', 0.0) or 0.0),
                'currency': data.get('currency', 'AUD')
            })
    else:
        next_id = max([b.get('id', 0) for b in bookings], default=0) + 1
        new_booking = {
            'id': next_id,
            'title': data.get('title', 'Untitled'),
            'date': data.get('date', ''),
            'location': data.get('location', ''),
            'notes': data.get('notes', ''),
            'cost': float(data.get('cost', 0.0) or 0.0),
            'currency': data.get('currency', 'AUD')
        }
        bookings.append(new_booking)

    save_bookings(bookings)
    return jsonify({'success': True, 'bookings': bookings})

@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    bookings = load_bookings()
    bookings = [b for b in bookings if b.get('id') != booking_id]
    save_bookings(bookings)
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
