"""Admin controllers for Vehicle Parking App."""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from models import db, ParkingLot, ParkingSpot, User, Reservation

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
def dashboard():
    """Admin dashboard showing all parking lots with statistics."""
    lots = ParkingLot.query.all()
    users = User.query.all()

    # Statistics for dashboard cards and charts
    total_lots = ParkingLot.query.count()
    total_spots = ParkingSpot.query.count()
    occupied_spots = ParkingSpot.query.filter_by(status="O").count()
    available_spots = total_spots - occupied_spots

    return render_template(
        "admin/dashboard.html",
        lots=lots,
        users=users,
        total_lots=total_lots,
        total_spots=total_spots,
        occupied_spots=occupied_spots,
        available_spots=available_spots,
    )

# ------------------------------------------------------------------
# User management
# ------------------------------------------------------------------
@bp.route("/users")
def list_users():
    """List all users for admin management."""
    users = User.query.all()
    return render_template("admin/users.html", users=users)


@bp.route("/users/delete/<int:user_id>", methods=["POST"])  # pragma: no cover
def delete_user(user_id: int):
    """Delete a user and related reservations."""
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash("Cannot delete an admin user", "danger")
        return redirect(url_for("admin.list_users"))

    try:
        # delete reservations first to maintain FK constraints
        Reservation.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to delete user: " + str(e), "danger")

    return redirect(url_for("admin.list_users"))


@bp.route("/add", methods=["GET", "POST"], endpoint="add_parking_lot")
def add_parking_lot():
    """Add a new parking lot."""
    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        address = request.form.get("address")
        pincode = request.form.get("pincode")
        price_per_hour = float(request.form.get("price_per_hour"))
        max_spots = int(request.form.get("max_spots"))

        # Create new parking lot
        lot = ParkingLot(
            name=name,
            address=address,
            pincode=pincode,
            price_per_hour=price_per_hour,
            max_spots=max_spots,
        )
        db.session.add(lot)
        db.session.commit()

        # Create spots for this lot
        for i in range(1, max_spots + 1):
            spot = ParkingSpot(lot_id=lot.id)
            db.session.add(spot)
        db.session.commit()

        flash("Parking lot created successfully!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/add_lot.html")

# ------------------------------------------------------------------
# Parking lot deletion
# ------------------------------------------------------------------
@bp.route("/lots/delete/<int:lot_id>", methods=["POST"])  # pragma: no cover
def delete_lot(lot_id: int):
    """Delete a parking lot and its spots/reservations."""
    lot = ParkingLot.query.get_or_404(lot_id)
    try:
        # Delete reservations linked to spots in this lot
        spot_ids = [s.id for s in lot.spots]
        if spot_ids:
            Reservation.query.filter(Reservation.spot_id.in_(spot_ids)).delete(synchronize_session=False)
        # Deleting the lot cascades delete spots (defined in model)
        db.session.delete(lot)
        db.session.commit()
        flash("Parking lot deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to delete lot: " + str(e), "danger")

    return redirect(url_for("admin.dashboard"))
