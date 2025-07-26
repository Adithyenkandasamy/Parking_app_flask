"""Database models and SQLAlchemy instance for Vehicle Parking App."""
from __future__ import annotations

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

# Create the SQLAlchemy instance (initialised later in app factory)
db: SQLAlchemy = SQLAlchemy()

__all__ = [
    "db",
    "User",
    "ParkingLot",
    "ParkingSpot",
    "Reservation",
]


class User(db.Model):
    """Users – both admin and normal users."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120))
    address = db.Column(db.String(255))
    pincode = db.Column(db.String(10))
    is_admin = db.Column(db.Boolean, default=False)

    reservations = db.relationship("Reservation", back_populates="user")

    # ---------------------------------------------------------------------
    # Convenience helpers
    # ---------------------------------------------------------------------
    def set_password(self, password: str) -> None:  # pragma: no cover
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:  # pragma: no cover
        return check_password_hash(self.password_hash, password)


class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    max_spots = db.Column(db.Integer, nullable=False)

    spots = db.relationship("ParkingSpot", back_populates="lot", cascade="all, delete-orphan")


class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey("parking_lot.id"), nullable=False)
    status = db.Column(db.String(1), default="A")  # A = Available, O = Occupied

    lot = db.relationship("ParkingLot", back_populates="spots")
    reservation = db.relationship("Reservation", back_populates="spot", uselist=False)


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey("parking_spot.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    parked_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime)

    spot = db.relationship("ParkingSpot", back_populates="reservation")
    user = db.relationship("User", back_populates="reservations")
