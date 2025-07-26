"""API endpoints for Vehicle Parking App."""
from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from models import db, ParkingLot, ParkingSpot, Reservation

bp = Blueprint("api", __name__, url_prefix="/api")


def format_reservation(reservation: Reservation) -> Dict[str, Any]:
    """Format a reservation for API response."""
    return {
        "id": reservation.id,
        "lot_id": reservation.spot.lot_id,
        "lot_name": reservation.spot.lot.name,
        "spot_id": reservation.spot_id,
        "spot_number": reservation.spot.id,
        "parked_at": reservation.parked_at.isoformat(),
        "left_at": reservation.left_at and reservation.left_at.isoformat(),
        "duration_hours": reservation.left_at and 
            round((reservation.left_at - reservation.parked_at).total_seconds() / 3600, 2),
        "cost": reservation.left_at and 
            round((reservation.left_at - reservation.parked_at).total_seconds() / 3600 * 
                  reservation.spot.lot.price_per_hour, 2)
    }


def format_parking_lot(lot: ParkingLot) -> Dict[str, Any]:
    """Format a parking lot for API response."""
    return {
        "id": lot.id,
        "name": lot.name,
        "address": lot.address,
        "pincode": lot.pincode,
        "price_per_hour": lot.price_per_hour,
        "max_spots": lot.max_spots,
        "available_spots": len([s for s in lot.spots if s.status == "A"]),
        "occupied_spots": len([s for s in lot.spots if s.status == "O"])
    }


@bp.route("/lots", methods=["GET"])
@login_required
def get_parking_lots():
    """Get all parking lots."""
    lots = ParkingLot.query.all()
    return jsonify([format_parking_lot(lot) for lot in lots])


@bp.route("/lots/<int:lot_id>", methods=["GET"])
@login_required
def get_parking_lot(lot_id: int):
    """Get a specific parking lot."""
    lot = ParkingLot.query.get_or_404(lot_id)
    return jsonify(format_parking_lot(lot))


@bp.route("/lots/<int:lot_id>/spots", methods=["GET"])
@login_required
def get_parking_spots(lot_id: int):
    """Get all spots for a parking lot."""
    lot = ParkingLot.query.get_or_404(lot_id)
    return jsonify({
        "lot": format_parking_lot(lot),
        "spots": [
            {
                "id": spot.id,
                "status": spot.status,
                "is_available": spot.status == "A"
            }
            for spot in lot.spots
        ]
    })


@bp.route("/history", methods=["GET"])
@login_required
def get_user_history():
    """Get user's parking history."""
    history = Reservation.query.filter_by(user_id=current_user.id)\
        .order_by(Reservation.parked_at.desc())\
        .all()
    return jsonify([format_reservation(res) for res in history])


@bp.route("/stats", methods=["GET"])
@login_required
def get_statistics():
    """Get parking statistics."""
    # Get all reservations
    reservations = Reservation.query.all()
    
    # Calculate statistics
    stats = {
        "total_parking_lots": ParkingLot.query.count(),
        "total_spots": ParkingSpot.query.count(),
        "total_bookings": len(reservations),
        "active_bookings": len([r for r in reservations if not r.left_at]),
        "revenue": round(sum(
            (r.left_at - r.parked_at).total_seconds() / 3600 * 
            r.spot.lot.price_per_hour
            for r in reservations if r.left_at
        ), 2),
        "usage_by_hour": {
            hour: len([r for r in reservations 
                      if r.parked_at.hour == hour and r.left_at])
            for hour in range(24)
        },
        "top_lots": [
            {
                "lot": format_parking_lot(lot),
                "bookings": len([r for r in reservations 
                                if r.spot.lot_id == lot.id])
            }
            for lot in ParkingLot.query.all()
        ]
    }
    
    return jsonify(stats)
