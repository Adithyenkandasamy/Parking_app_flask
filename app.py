"""Entry point for Vehicle Parking App - V1.

This file wires together Flask, SQLAlchemy and the initial blueprints / routes.
Keeping everything in a single file for the very first skeleton keeps the
project runnable with the least friction. As the feature-set grows we will
split blueprints and controllers into the `controllers/` package.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv
from datetime import datetime

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    send_from_directory,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from typing import Optional
import glob
import click

# ----------------------------------------------------------------------------
# Flask & DB setup
# ----------------------------------------------------------------------------
# Load variables from .env file if present
load_dotenv()

app = Flask(__name__)
# NOTE: Change this key in production
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads", "profile")

db = SQLAlchemy(app)

# ----------------------------------------------------------------------------
# Database models
# ----------------------------------------------------------------------------
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

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
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


class Waitlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey("parking_lot.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified = db.Column(db.Boolean, default=False)


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey("parking_spot.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    parked_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime)

    spot = db.relationship("ParkingSpot", back_populates="reservation")
    user = db.relationship("User", back_populates="reservations")


# ----------------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------------

def bootstrap_database() -> None:
    """Create tables + default admin if DB does not exist yet."""

    # All DB operations require an application context.
    with app.app_context():
        db.create_all()

        # Ensure admin exists
        admin = User.query.filter_by(is_admin=True).first()
        if admin is None:
            admin_username = os.getenv("ADMIN_USERNAME", "admin")
            admin_password = os.getenv("ADMIN_PASSWORD", "admin")
            admin = User(username=admin_username, is_admin=True)
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            app.logger.info("Default admin created (username='admin', password='admin')")
        # Ensure upload directory exists
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# ----------------------------------------------------------------------------
# Routes – minimal set to verify skeleton works
# ----------------------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user and user.is_admin:
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("user_dashboard"))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session["user_id"] = user.id
        flash("Logged in successfully", "success")
        if user.is_admin:
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("user_dashboard"))

    flash("Invalid credentials", "danger")
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out", "info")
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        full_name = request.form.get("full_name")
        address = request.form.get("address")
        pincode = request.form.get("pincode")

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "warning")
            return redirect(url_for("register"))
        user = User(username=username, full_name=full_name, address=address, pincode=pincode)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/admin")
def admin_dashboard():
    user = _get_current_user()
    if not user or not user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for("index"))
    lots = ParkingLot.query.all()

    # statistics for cards and chart
    total_lots = ParkingLot.query.count()
    total_spots = ParkingSpot.query.count()
    occupied_spots = ParkingSpot.query.filter_by(status="O").count()
    available_spots = total_spots - occupied_spots

    return render_template(
        "admin/dashboard.html",
        user=user,
        lots=lots,
        total_lots=total_lots,
        total_spots=total_spots,
        occupied_spots=occupied_spots,
        available_spots=available_spots,
    )

# -----------------------------------------------------------------------------
# Admin – user management
# -----------------------------------------------------------------------------
@app.route("/admin/users")
def admin_list_users():
    user = _get_current_user()
    if not user or not user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for("index"))

    users = User.query.all()
    return render_template("admin/users.html", user=user, users=users)


@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
def admin_delete_user(user_id: int):
    user = _get_current_user()
    if not user or not user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for("index"))

    target = User.query.get_or_404(user_id)
    if target.is_admin:
        flash("Cannot delete another admin user", "danger")
        return redirect(url_for("admin_list_users"))

    try:
        Reservation.query.filter_by(user_id=user_id).delete()
        db.session.delete(target)
        db.session.commit()
        flash("User deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to delete user: " + str(e), "danger")

    return redirect(url_for("admin_list_users"))


@app.route("/user")
def user_dashboard():
    user = _get_current_user()
    if not user or user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for("index"))
    # Data needed for dashboard
    lots = ParkingLot.query.all()

    active_reservation = Reservation.query.filter_by(
        user_id=user.id,
        left_at=None
    ).first()

    history = Reservation.query.filter_by(user_id=user.id).order_by(
        Reservation.parked_at.desc()
    ).all()

    return render_template(
        "user/dashboard.html",
        user=user,
        lots=lots,
        active_reservation=active_reservation,
        history=history,
    )


# -----------------------------------------------------------------------------
# User booking & release routes
# -----------------------------------------------------------------------------
@app.route("/user/book/<int:lot_id>")
def book_parking(lot_id: int):
    """Book parking in a specific lot."""
    user = _get_current_user()
    if not user or user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for("index"))

    lot = ParkingLot.query.get_or_404(lot_id)

    # If user already has active reservation
    active_res = Reservation.query.filter_by(user_id=user.id, left_at=None).first()
    if active_res:
        flash("You already have an active reservation.", "warning")
        return redirect(url_for("user_dashboard"))

    # Find an available spot in the lot
    spot = ParkingSpot.query.filter_by(lot_id=lot_id, status="A").first()
    if not spot:
        flash("No available spots in this lot", "danger")
        return redirect(url_for("user_dashboard"))

    try:
        res = Reservation(spot_id=spot.id, user_id=user.id)
        db.session.add(res)
        spot.status = "O"
        db.session.commit()
        flash("Parking booked successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to book parking: {e}", "danger")

    return redirect(url_for("user_dashboard"))


@app.route("/user/waitlist/<int:lot_id>")
def join_waitlist(lot_id: int):
    """Add current user to waitlist for a lot if full."""
    user = _get_current_user()
    if not user or user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for("index"))

    # Already waitlisted?
    existing = Waitlist.query.filter_by(lot_id=lot_id, user_id=user.id, notified=False).first()
    if existing:
        flash("You are already on the waitlist for this lot.", "info")
        return redirect(url_for("user_dashboard"))

    wl = Waitlist(lot_id=lot_id, user_id=user.id)
    db.session.add(wl)
    db.session.commit()
    flash("You have been added to the waitlist. We will notify you when a spot opens up.", "success")
    return redirect(url_for("user_dashboard"))


@app.route("/user/release/<int:reservation_id>")
def release_parking(reservation_id: int):
    """Release a parking spot and calculate cost."""
    user = _get_current_user()
    if not user or user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for("index"))

    try:
        reservation = Reservation.query.filter_by(id=reservation_id, user_id=user.id, left_at=None).first_or_404()
        duration = datetime.utcnow() - reservation.parked_at
        hours = duration.total_seconds() / 3600
        cost = round(hours * reservation.spot.lot.price_per_hour, 2)

        reservation.left_at = datetime.utcnow()
        reservation.spot.status = "A"
        db.session.commit()
        flash(f"Parking spot released successfully! Total cost: ₹{cost}", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to release parking: {e}", "danger")

    return redirect(url_for("user_dashboard"))



@app.route("/admin/add", methods=["GET", "POST"])
def admin_add_parking_lot():
    """Add a new parking lot via admin interface."""
    user = _get_current_user()
    if not user or not user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name")
        address = request.form.get("address")
        pincode = request.form.get("pincode")
        price_per_hour = float(request.form.get("price_per_hour"))
        max_spots = int(request.form.get("max_spots"))

        lot = ParkingLot(
            name=name,
            address=address,
            pincode=pincode,
            price_per_hour=price_per_hour,
            max_spots=max_spots,
        )
        db.session.add(lot)
        db.session.commit()

        # Create parking spots
        for _ in range(max_spots):
            spot = ParkingSpot(lot_id=lot.id)
            db.session.add(spot)
        db.session.commit()

        flash("Parking lot created successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/add_lot.html", user=user)

# -----------------------------------------------------------------------------
# Profile image upload and serving
# -----------------------------------------------------------------------------

def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"png", "jpg", "jpeg", "webp"}


@app.route("/user/profile/upload", methods=["POST"])
def upload_profile_image():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in first.", "warning")
        return redirect(url_for("index"))

    file = request.files.get("image")
    if not file or file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("user_dashboard"))
    if not _allowed_file(file.filename):
        flash("Invalid file type. Allowed: png, jpg, jpeg, webp", "danger")
        return redirect(url_for("user_dashboard"))

    # Save using user_id with original extension
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{user_id}.{ext}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    try:
        file.save(save_path)
        flash("Profile image updated.", "success")
    except Exception as e:
        app.logger.exception("Failed to save uploaded image: %s", e)
        flash("Failed to upload image.", "danger")
    return redirect(url_for("user_dashboard"))


@app.route("/uploads/profile/<path:filename>")
def serve_profile_image(filename: str):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/user/profile/current")
def serve_profile_current():
    user_id = session.get("user_id")
    if not user_id:
        # No image for anonymous
        return ("", 404)
    # Find any file with user_id.* in UPLOAD_FOLDER
    pattern = os.path.join(app.config["UPLOAD_FOLDER"], f"{user_id}.*")
    matches = glob.glob(pattern)
    if not matches:
        return ("", 404)
    # Serve the first match
    fname = os.path.basename(matches[0])
    return send_from_directory(app.config["UPLOAD_FOLDER"], fname)

# ----------------------------------------------------------------------------
# Context & utilities
# ----------------------------------------------------------------------------

def _get_current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


# ----------------------------------------------------------------------------
# CLI helpers
# ----------------------------------------------------------------------------
@app.cli.command("init-db")
def init_db_cmd():  # pragma: no cover
    """Flask CLI: `flask init-db` to bootstrap database."""

    bootstrap_database()
    click.echo("Database initialized with default admin user.")


# ----------------------------------------------------------------------------
# Main entry
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    bootstrap_database()
    app.run(debug=True)
