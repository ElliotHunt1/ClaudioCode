from flask import Flask, render_template, request, jsonify, session
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Data storage paths
BOOKINGS_FILE = 'data/bookings.json'
ITINERARY_FILE = 'data/itinerary.json'

# Ensure data directories exist
os.makedirs('data', exist_ok=True)

def load_bookings():
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_bookings(bookings):
    with open(BOOKINGS_FILE, 'w') as f:
        json.dump(bookings, f, indent=2)

def load_itinerary():
    if os.path.exists(ITINERARY_FILE):
        with open(ITINERARY_FILE, 'r') as f:
            return json.load(f)
    # Default 21-day itinerary structure
    return [{'day': i+1, 'date': '', 'locations': [], 'activities': [], 'notes': ''} for i in range(21)]

def save_itinerary(itinerary):
    with open(ITINERARY_FILE, 'w') as f:
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

def safe_float(value):
    try:
        if value is None or value == '':
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

@app.route('/api/budget/calculate', methods=['POST'])
def calculate_budget():
    data = request.json or {}
    # Simple budget calculation
    flights = safe_float(data.get('flights', 0))
    accommodation = safe_float(data.get('accommodation', 0))
    food = safe_float(data.get('food', 0))
    activities = safe_float(data.get('activities', 0))
    transport = safe_float(data.get('transport', 0))
    misc = safe_float(data.get('misc', 0))
    
    subtotal = flights + accommodation + food + activities + transport + misc
    # Assume 10% contingency
    total = subtotal * 1.1
    
    return jsonify({
        'subtotal': round(subtotal, 2),
        'contingency': round(subtotal * 0.1, 2),
        'total': round(total, 2),
        'currency': 'AUD'
    })

@app.route('/api/itinerary/update', methods=['POST'])
def update_itinerary():
    data = request.json
    itinerary = load_itinerary()
    
    day_index = data['day'] - 1
    if 0 <= day_index < len(itinerary):
        itinerary[day_index] = data
        save_itinerary(itinerary)
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid day'}), 400

@app.route('/api/bookings', methods=['GET', 'POST'])
def handle_bookings():
    if request.method == 'GET':
        return jsonify(load_bookings())
    
    data = request.json
    
    bookings = load_bookings()
    
    if 'id' in data:
        # Update existing
        for i, booking in enumerate(bookings):
            if booking['id'] == data['id']:
                bookings[i] = data
                break
    else:
        # Add new
        data['id'] = len(bookings) + 1
        bookings.append(data)
    
    save_bookings(bookings)
    return jsonify({'success': True, 'booking': data})

@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    bookings = load_bookings()
    bookings = [b for b in bookings if b['id'] != booking_id]
    save_bookings(bookings)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)