from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin | staff | trekker
    status = db.Column(db.String(20), default="pending")

    bookings = db.relationship("Booking", backref="user", lazy=True)
    managed_treks = db.relationship(
        "Trek",
        backref="assigned_staff",
        lazy=True,
        foreign_keys="Trek.staff_id",
    )


class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    duration = db.Column(db.Integer)
    available_slots = db.Column(db.Integer)
    status = db.Column(db.String(20), default="Pending")
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    staff_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    bookings = db.relationship("Booking", backref="trek", lazy=True)


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    booking_date = db.Column(db.Date)
    status = db.Column(db.String(20), default="Booked")
