# Vehicle Parking Management System

## Project Overview

The Vehicle Parking Management System is a web-based application built using Flask that provides a comprehensive solution for managing parking lots and parking spots for 4-wheelers. The system includes both admin and user dashboards with features for managing parking lots, booking spots, and tracking usage statistics.

## Features

### Admin Dashboard
- Add/Edit/Delete parking lots
- View parking spot status (Available/Occupied)
- View user list and booking history
- Generate usage statistics and charts
- Manage parking lot pricing and capacity

### User Dashboard
- Search and book available parking spots
- View active booking and release parking spot
- View parking history with cost calculations
- Responsive design for mobile and desktop

### API Features
- RESTful API endpoints for parking lots and spots
- User booking history API
- Statistics and analytics API
- Real-time spot availability updates

### Charts and Analytics
- Hourly usage patterns
- Top parking lots by usage
- Usage timeline
- Revenue statistics

## Technical Stack

### Backend
- Flask (Python web framework)
- SQLAlchemy (ORM)
- SQLite (Database)
- Werkzeug (Security)
- Flask-Login (Authentication)

### Frontend
- Bootstrap 5 (UI Framework)
- Chart.js (Data Visualization)
- Bootstrap Icons (UI Icons)
- HTML5/CSS3/JavaScript

## Database Schema

### Tables
1. Users
   - id
   - username
   - password_hash
   - full_name
   - address
   - pincode
   - is_admin

2. ParkingLots
   - id
   - name
   - address
   - pincode
   - price_per_hour
   - max_spots

3. ParkingSpots
   - id
   - lot_id
   - status (A/O)

4. Reservations
   - id
   - spot_id
   - user_id
   - parked_at
   - left_at

## Installation Guide

1. Install Python 3.8+
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Create .env file with admin credentials
4. Initialize database:
   ```bash
   flask init-db
   ```
5. Run the application:
   ```bash
   python app.py
   ```

## Usage

### Admin Access
1. Login with admin credentials from .env file
2. Access admin dashboard at /admin
3. Manage parking lots and view statistics

### User Access
1. Register a new account
2. Login with credentials
3. Book available parking spots
4. View and release active bookings

## Security Features

- Password hashing using Werkzeug
- Secure session management
- Input validation
- CSRF protection
- Rate limiting

## Future Enhancements

1. Real-time spot availability updates
2. Mobile app integration
3. Payment gateway integration
4. Advanced analytics
5. Multi-language support

## Conclusion

The Vehicle Parking Management System provides a robust solution for managing parking lots and spots. It offers a user-friendly interface for both administrators and users while maintaining security and scalability. The system is designed to be easily maintainable and extensible for future enhancements.
