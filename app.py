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
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
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
    return render_template("admin/dashboard.html", user=user, lots=lots)


@app.route("/user")
def user_dashboard():
    user = _get_current_user()
    if not user or user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for("index"))
    reservations = Reservation.query.filter_by(user_id=user.id).all()
    return render_template("user/dashboard.html", user=user, reservations=reservations)


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
