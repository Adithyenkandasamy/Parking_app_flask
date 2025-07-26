"""User controllers for Vehicle Parking App."""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user

from models import db, ParkingLot, ParkingSpot, Reservation

bp = Blueprint("user", __name__, url_prefix="/user")


@bp.route("/")
def dashboard():
    """User dashboard showing available parking lots and booking history."""
    # Get all available parking lots
    lots = ParkingLot.query.all()
    
    # Get user's active reservation
    active_reservation = None
    if current_user.is_authenticated:
        active_reservation = Reservation.query.filter_by(
            user_id=current_user.id,
            left_at=None
        ).first()

    # Get user's reservation history
    history = Reservation.query.filter_by(
        user_id=current_user.id
    ).order_by(Reservation.parked_at.desc()).all()

    return render_template(
        "user/dashboard.html",
        lots=lots,
        active_reservation=active_reservation,
        history=history
    )


@bp.route("/book/<int:lot_id>")
def book_parking(lot_id: int):
    """Book parking in a specific lot."""
    if not current_user.is_authenticated:
        flash("Please login to book parking", "warning")
        return redirect(url_for("index"))

    lot = ParkingLot.query.get_or_404(lot_id)
    
    # Check if user already has an active reservation
    active_reservation = Reservation.query.filter_by(
        user_id=current_user.id,
        left_at=None
    ).first()
    
    if active_reservation:
        flash("You already have an active reservation.", "warning")
        return redirect(url_for("user.dashboard"))

    # Find first available spot
    available_spot = ParkingSpot.query.filter_by(
        lot_id=lot_id,
        status="A"
    ).first()

    if not available_spot:
        flash("No spots available in this lot", "danger")
        return redirect(url_for("user.dashboard"))

    try:
        # Create reservation
        reservation = Reservation(
            spot_id=available_spot.id,
            user_id=current_user.id
        )
        db.session.add(reservation)
        
        # Update spot status to occupied
        available_spot.status = "O"
        
        db.session.commit()
        flash("Parking booked successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to book parking: " + str(e), "danger")

    return redirect(url_for("user.dashboard"))


@bp.route("/release/<int:reservation_id>")
def release_parking(reservation_id: int):
    """Release a parking spot."""
    if not current_user.is_authenticated:
        flash("Please login to release parking", "warning")
        return redirect(url_for("index"))

    try:
        reservation = Reservation.query.filter_by(
            id=reservation_id,
            user_id=current_user.id,
            left_at=None
        ).first_or_404()

        # Calculate duration
        duration = datetime.utcnow() - reservation.parked_at
        hours = duration.total_seconds() / 3600
        cost = round(hours * reservation.spot.lot.price_per_hour, 2)

        # Update reservation
        reservation.left_at = datetime.utcnow()
        
        # Update spot status to available
        spot = ParkingSpot.query.get(reservation.spot_id)
        spot.status = "A"
        
        db.session.commit()
        
        flash(f"Parking spot released successfully! Total cost: ₹{cost}", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to release parking: " + str(e), "danger")

    return redirect(url_for("user.dashboard"))
