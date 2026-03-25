# ClaudioCode

## Australia Trip Planner

A modern, sleek web application for planning a 3-week trip to Australia. Features include budget calculation, itinerary planning, and booking management.

### Features

- **Budget Calculator**: Track costs for flights, accommodation, food, activities, transport, and miscellaneous expenses with automatic contingency calculation
- **Itinerary Planner**: Plan your 21-day journey with locations, activities, and notes for each day
- **Booking Manager**: Store and organize flight, hotel, tour, and transport bookings with confirmation details
- **Modern UI**: Responsive design with Tailwind CSS, gradients, and smooth animations

### Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. Open your browser to `http://localhost:5000`

### Project Structure

```
ClaudioCode/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── index.html        # Dashboard
│   ├── budget.html       # Budget calculator
│   ├── itinerary.html    # Itinerary planner
│   └── bookings.html     # Booking manager
├── data/                  # Data storage (created automatically)
│   ├── bookings.json     # Booking data
│   └── itinerary.json    # Itinerary data
└── README.md             # This file
```

### Usage

- **Dashboard**: Navigate to different sections
- **Budget**: Enter costs in each category and calculate total with contingency
- **Itinerary**: Fill in details for each of the 21 days
- **Bookings**: Add, view, and delete booking information

### Technologies

- **Backend**: Python Flask
- **Frontend**: HTML, CSS (Tailwind), JavaScript
- **Data Storage**: JSON files (local)
- **Icons**: Font Awesome

### Future Enhancements

- User authentication
- Database integration (SQLite/PostgreSQL)
- Export functionality (PDF/CSV)
- Weather API integration
- Map integration for locations