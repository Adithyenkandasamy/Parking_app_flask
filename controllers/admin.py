"""Admin controllers for Vehicle Parking App."""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from models import db, ParkingLot, ParkingSpot

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
def dashboard():
    """Admin dashboard showing all parking lots with statistics."""
    lots = ParkingLot.query.all()

    # Statistics for dashboard cards and charts
    total_lots = ParkingLot.query.count()
    total_spots = ParkingSpot.query.count()
    occupied_spots = ParkingSpot.query.filter_by(status="O").count()
    available_spots = total_spots - occupied_spots

    return render_template(
        "admin/dashboard.html",
        lots=lots,
        total_lots=total_lots,
        total_spots=total_spots,
        occupied_spots=occupied_spots,
        available_spots=available_spots,
    )


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
