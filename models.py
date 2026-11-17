from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin | examiner | student
    status = db.Column(db.String(20), default="approved")  # approved | pending | inactive
    department = db.Column(db.String(100), default="Computer Science")
    contact = db.Column(db.String(50), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    slots = db.relationship("ExamSlot", backref="examiner", lazy=True)
    bookings = db.relationship("Booking", backref="student", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_active(self):
        return self.status == "approved"


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="active")  # active | archived
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    examinations = db.relationship("Examination", backref="course", lazy=True, cascade="all, delete-orphan")


class Examination(db.Model):
    __tablename__ = "examinations"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False, default="Viva")  # Viva | Practical | Project Demo | Assessment
    duration = db.Column(db.Integer, default=30)  # minutes
    max_marks = db.Column(db.Float, default=100.0)
    slot_creation_start = db.Column(db.DateTime, nullable=True)
    slot_creation_end = db.Column(db.DateTime, nullable=True)
    booking_start = db.Column(db.DateTime, nullable=True)
    booking_end = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(30), default="Draft")  # Draft | Slot Creation | Booking Open | Closed | Completed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    rubrics = db.relationship("Rubric", backref="examination", lazy=True, cascade="all, delete-orphan")
    slots = db.relationship("ExamSlot", backref="examination", lazy=True, cascade="all, delete-orphan")

    def is_slot_creation_active(self):
        if self.status != "Slot Creation":
            return False
        now = datetime.now()
        if self.slot_creation_start and now < self.slot_creation_start:
            return False
        if self.slot_creation_end and now > self.slot_creation_end:
            return False
        return True

    def is_booking_active(self):
        if self.status != "Booking Open":
            return False
        now = datetime.now()
        if self.booking_start and now < self.booking_start:
            return False
        if self.booking_end and now > self.booking_end:
            return False
        return True


class Rubric(db.Model):
    __tablename__ = "rubrics"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("examinations.id"), nullable=False)
    criterion_name = db.Column(db.String(150), nullable=False)
    max_marks = db.Column(db.Float, nullable=False, default=20.0)
    weightage = db.Column(db.Float, default=100.0)
    description = db.Column(db.Text, default="")

    evaluations = db.relationship("Evaluation", backref="rubric", lazy=True, cascade="all, delete-orphan")


class ExamSlot(db.Model):
    __tablename__ = "exam_slots"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("examinations.id"), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(10), nullable=False)  # HH:MM
    end_time = db.Column(db.String(10), nullable=False)    # HH:MM
    capacity = db.Column(db.Integer, default=1, nullable=False)
    available_seats = db.Column(db.Integer, default=1, nullable=False)
    status = db.Column(db.String(20), default="Available")  # Available | Full | Cancelled | Completed

    bookings = db.relationship("Booking", backref="slot", lazy=True, cascade="all, delete-orphan")


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("exam_slots.id"), nullable=False)
    booking_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default="Booked")  # Booked | Cancelled | Completed

    evaluations = db.relationship("Evaluation", backref="booking", lazy=True, cascade="all, delete-orphan")

    @property
    def total_score(self):
        if not self.evaluations:
            return None
        return sum(e.marks_awarded for e in self.evaluations)

    @property
    def is_evaluated(self):
        return len(self.evaluations) > 0 and self.status == "Completed"


class Evaluation(db.Model):
    __tablename__ = "evaluations"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey("rubrics.id"), nullable=False)
    marks_awarded = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.Text, default="")
    evaluated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
