from datetime import date, datetime, timezone
from functools import wraps
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from models import Booking, Course, Evaluation, ExamSlot, Examination, Rubric, User, db

app = Flask(__name__)
app.config["SECRET_KEY"] = "emp-mad1-secret-key-iitm-2026"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///emp.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# ---------------------------------------------------------
# Helper Functions & Access Control Decorators
# ---------------------------------------------------------
def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login"))
            user = current_user()
            if not user or user.status != "approved":
                session.clear()
                flash("Account is not active or approved.", "danger")
                return redirect(url_for("login"))
            if user.role not in allowed_roles:
                flash("Access denied: You do not have permission for this section.", "danger")
                if user.role == "admin":
                    return redirect(url_for("admin_dashboard"))
                elif user.role == "examiner":
                    return redirect(url_for("examiner_dashboard"))
                elif user.role == "student":
                    return redirect(url_for("student_dashboard"))
                return redirect(url_for("login"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


@app.context_processor
def inject_user_context():
    return {
        "current_user": current_user(),
        "current_role": session.get("role"),
        "now": datetime.now(),
    }


# ---------------------------------------------------------
# Public & Authentication Routes
# ---------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        role = session.get("role")
        if role == "admin":
            return redirect(url_for("admin_dashboard"))
        elif role == "examiner":
            return redirect(url_for("examiner_dashboard"))
        elif role == "student":
            return redirect(url_for("student_dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email address or password.", "danger")
            return render_template("login.html")

        if user.status == "pending":
            flash("Your examiner account is pending Admin approval. Please contact administrator.", "warning")
            return render_template("login.html")

        if user.status == "inactive":
            flash("Your account has been deactivated. Please contact administrator.", "danger")
            return render_template("login.html")

        session["user_id"] = user.id
        session["role"] = user.role
        session["user_name"] = user.name

        flash(f"Welcome back, {user.name}!", "success")
        if user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        elif user.role == "examiner":
            return redirect(url_for("examiner_dashboard"))
        elif user.role == "student":
            return redirect(url_for("student_dashboard"))
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Only Examiners and Students can register. Admin is strictly pre-seeded.
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "")
        department = request.form.get("department", "").strip()
        contact = request.form.get("contact", "").strip()

        if role not in ["examiner", "student"]:
            flash("Invalid registration role specified.", "danger")
            return render_template("register.html")

        if not name or not email or not password:
            flash("All mandatory fields must be filled.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email address already exists.", "danger")
            return render_template("register.html")

        # Students are automatically approved; Examiners require Admin approval
        initial_status = "pending" if role == "examiner" else "approved"

        new_user = User(
            name=name,
            email=email,
            role=role,
            status=initial_status,
            department=department,
            contact=contact,
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        if role == "examiner":
            flash("Registration successful! Your examiner account is pending admin approval.", "info")
        else:
            flash("Registration successful! You may now log in to the portal.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have successfully logged out.", "info")
    return redirect(url_for("login"))


@app.route("/profile", methods=["GET", "POST"])
@role_required("admin", "examiner", "student")
def profile():
    user = current_user()
    if request.method == "POST":
        user.name = request.form.get("name", user.name).strip()
        user.department = request.form.get("department", user.department).strip()
        user.contact = request.form.get("contact", user.contact).strip()

        new_pass = request.form.get("new_password", "").strip()
        if new_pass:
            user.set_password(new_pass)
            flash("Profile and password updated successfully.", "success")
        else:
            flash("Profile updated successfully.", "success")

        db.session.commit()
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)


# ---------------------------------------------------------
# Admin Functionalities
# ---------------------------------------------------------
@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    keyword = request.args.get("search", "").strip()

    total_courses = Course.query.count()
    total_exams = Examination.query.count()
    total_examiners = User.query.filter_by(role="examiner").count()
    total_students = User.query.filter_by(role="student").count()
    pending_examiners_count = User.query.filter_by(role="examiner", status="pending").count()
    total_slots = ExamSlot.query.count()
    total_bookings = Booking.query.count()

    matched_students = []
    matched_examiners = []
    matched_exams = []
    matched_bookings = []

    if keyword:
        # Search by name or email or ID
        matched_students = (
            User.query.filter(User.role == "student")
            .filter((User.name.ilike(f"%{keyword}%")) | (User.email.ilike(f"%{keyword}%")))
            .all()
        )
        matched_examiners = (
            User.query.filter(User.role == "examiner")
            .filter((User.name.ilike(f"%{keyword}%")) | (User.email.ilike(f"%{keyword}%")))
            .all()
        )
        matched_exams = (
            Examination.query.filter(Examination.name.ilike(f"%{keyword}%"))
            .all()
        )
        if keyword.isdigit():
            b_by_id = Booking.query.get(int(keyword))
            if b_by_id:
                matched_bookings.append(b_by_id)

    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(8).all()
    recent_exams = Examination.query.order_by(Examination.created_at.desc()).limit(6).all()

    return render_template(
        "admin_dashboard.html",
        total_courses=total_courses,
        total_exams=total_exams,
        total_examiners=total_examiners,
        total_students=total_students,
        pending_examiners_count=pending_examiners_count,
        total_slots=total_slots,
        total_bookings=total_bookings,
        search=keyword,
        matched_students=matched_students,
        matched_examiners=matched_examiners,
        matched_exams=matched_exams,
        matched_bookings=matched_bookings,
        recent_bookings=recent_bookings,
        recent_exams=recent_exams,
    )


# Admin: Course Management
@app.route("/admin/courses", methods=["GET", "POST"])
@role_required("admin")
def admin_courses():
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not code or not name:
            flash("Course code and title are required.", "danger")
        elif Course.query.filter_by(code=code).first():
            flash("Course code already exists.", "danger")
        else:
            course = Course(code=code, name=name, description=description, status="active")
            db.session.add(course)
            db.session.commit()
            flash("Course created successfully.", "success")
        return redirect(url_for("admin_courses"))

    courses = Course.query.order_by(Course.created_at.desc()).all()
    return render_template("admin_courses.html", courses=courses)


@app.route("/admin/courses/<int:course_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def admin_edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == "POST":
        course.code = request.form.get("code", "").strip().upper()
        course.name = request.form.get("name", "").strip()
        course.description = request.form.get("description", "").strip()
        course.status = request.form.get("status", "active")
        db.session.commit()
        flash("Course updated successfully.", "success")
        return redirect(url_for("admin_courses"))
    return render_template("admin_course_edit.html", course=course)


@app.route("/admin/courses/<int:course_id>/delete", methods=["POST"])
@role_required("admin")
def admin_delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course and related examinations deleted.", "info")
    return redirect(url_for("admin_courses"))


# Admin: Examination Management
@app.route("/admin/exams")
@role_required("admin")
def admin_exams():
    exams = Examination.query.order_by(Examination.created_at.desc()).all()
    return render_template("admin_exams.html", exams=exams)


@app.route("/admin/exams/create", methods=["GET", "POST"])
@role_required("admin")
def admin_create_exam():
    courses = Course.query.filter_by(status="active").all()
    if request.method == "POST":
        course_id = int(request.form.get("course_id"))
        name = request.form.get("name", "").strip()
        exam_type = request.form.get("exam_type", "Viva")
        duration = int(request.form.get("duration", 30))
        max_marks = float(request.form.get("max_marks", 100))
        status = request.form.get("status", "Draft")

        # Parse date timelines
        def parse_dt(field_val):
            if not field_val:
                return None
            try:
                return datetime.strptime(field_val, "%Y-%m-%dT%H:%M")
            except ValueError:
                return None

        slot_creation_start = parse_dt(request.form.get("slot_creation_start"))
        slot_creation_end = parse_dt(request.form.get("slot_creation_end"))
        booking_start = parse_dt(request.form.get("booking_start"))
        booking_end = parse_dt(request.form.get("booking_end"))

        exam = Examination(
            course_id=course_id,
            name=name,
            exam_type=exam_type,
            duration=duration,
            max_marks=max_marks,
            status=status,
            slot_creation_start=slot_creation_start,
            slot_creation_end=slot_creation_end,
            booking_start=booking_start,
            booking_end=booking_end,
        )
        db.session.add(exam)
        db.session.commit()
        flash("Examination created successfully. You may now define its evaluation rubrics.", "success")
        return redirect(url_for("admin_exam_rubrics", exam_id=exam.id))

    return render_template("admin_exam_form.html", title="Create Examination", courses=courses, exam=None)


@app.route("/admin/exams/<int:exam_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def admin_edit_exam(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    courses = Course.query.all()

    if request.method == "POST":
        exam.course_id = int(request.form.get("course_id"))
        exam.name = request.form.get("name", "").strip()
        exam.exam_type = request.form.get("exam_type", "Viva")
        exam.duration = int(request.form.get("duration", 30))
        exam.max_marks = float(request.form.get("max_marks", 100))
        exam.status = request.form.get("status", "Draft")

        def parse_dt(field_val):
            if not field_val:
                return None
            try:
                return datetime.strptime(field_val, "%Y-%m-%dT%H:%M")
            except ValueError:
                return None

        exam.slot_creation_start = parse_dt(request.form.get("slot_creation_start"))
        exam.slot_creation_end = parse_dt(request.form.get("slot_creation_end"))
        exam.booking_start = parse_dt(request.form.get("booking_start"))
        exam.booking_end = parse_dt(request.form.get("booking_end"))

        db.session.commit()
        flash("Examination details updated.", "success")
        return redirect(url_for("admin_exams"))

    return render_template("admin_exam_form.html", title="Edit Examination", courses=courses, exam=exam)


@app.route("/admin/exams/<int:exam_id>/status", methods=["POST"])
@role_required("admin")
def admin_update_exam_status(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    new_status = request.form.get("status")
    if new_status in ["Draft", "Slot Creation", "Booking Open", "Closed", "Completed"]:
        exam.status = new_status
        db.session.commit()
        flash(f"Examination status transitioned to '{new_status}'.", "info")
    return redirect(request.referrer or url_for("admin_exams"))


@app.route("/admin/exams/<int:exam_id>/delete", methods=["POST"])
@role_required("admin")
def admin_delete_exam(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    flash("Examination and related records deleted.", "info")
    return redirect(url_for("admin_exams"))


# Admin: Rubrics Management
@app.route("/admin/exams/<int:exam_id>/rubrics", methods=["GET", "POST"])
@role_required("admin")
def admin_exam_rubrics(exam_id):
    exam = Examination.query.get_or_404(exam_id)

    if request.method == "POST":
        criterion_name = request.form.get("criterion_name", "").strip()
        max_marks = float(request.form.get("max_marks", 20))
        weightage = float(request.form.get("weightage", 100))
        description = request.form.get("description", "").strip()

        rubric = Rubric(
            exam_id=exam.id,
            criterion_name=criterion_name,
            max_marks=max_marks,
            weightage=weightage,
            description=description,
        )
        db.session.add(rubric)
        db.session.commit()
        flash("Evaluation criterion added to rubric.", "success")
        return redirect(url_for("admin_exam_rubrics", exam_id=exam.id))

    return render_template("admin_rubrics.html", exam=exam)


@app.route("/admin/rubrics/<int:rubric_id>/delete", methods=["POST"])
@role_required("admin")
def admin_delete_rubric(rubric_id):
    rubric = Rubric.query.get_or_404(rubric_id)
    exam_id = rubric.exam_id
    db.session.delete(rubric)
    db.session.commit()
    flash("Rubric criterion removed.", "info")
    return redirect(url_for("admin_exam_rubrics", exam_id=exam_id))


# Admin: Examiner Management (Approve / Deactivate)
@app.route("/admin/examiners")
@role_required("admin")
def admin_examiners():
    examiners = User.query.filter_by(role="examiner").order_by(User.id.desc()).all()
    return render_template("admin_examiners.html", examiners=examiners)


@app.route("/admin/examiners/<int:user_id>/approve", methods=["POST"])
@role_required("admin")
def admin_approve_examiner(user_id):
    user = User.query.get_or_404(user_id)
    user.status = "approved"
    db.session.commit()
    flash(f"Examiner {user.name} has been approved.", "success")
    return redirect(url_for("admin_examiners"))


@app.route("/admin/examiners/<int:user_id>/toggle", methods=["POST"])
@role_required("admin")
def admin_toggle_examiner(user_id):
    user = User.query.get_or_404(user_id)
    user.status = "inactive" if user.status == "approved" else "approved"
    db.session.commit()
    flash(f"Status for {user.name} changed to {user.status}.", "info")
    return redirect(url_for("admin_examiners"))


# Admin: Slot Oversight & Reassignment
@app.route("/admin/slots")
@role_required("admin")
def admin_slots():
    slots = ExamSlot.query.order_by(ExamSlot.date.desc(), ExamSlot.start_time.asc()).all()
    approved_examiners = User.query.filter_by(role="examiner", status="approved").all()
    return render_template("admin_slots.html", slots=slots, examiners=approved_examiners)


@app.route("/admin/slots/<int:slot_id>/change_examiner", methods=["POST"])
@role_required("admin")
def admin_change_examiner(slot_id):
    slot = ExamSlot.query.get_or_404(slot_id)
    new_examiner_id = int(request.form.get("examiner_id"))
    new_examiner = User.query.filter_by(id=new_examiner_id, role="examiner").first_or_404()

    slot.examiner_id = new_examiner.id
    db.session.commit()
    flash(f"Assigned examiner for Slot #{slot.id} changed to {new_examiner.name}.", "success")
    return redirect(url_for("admin_slots"))


# Admin: Booking Oversight & Rescheduling
@app.route("/admin/bookings")
@role_required("admin")
def admin_bookings():
    bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template("admin_bookings.html", bookings=bookings)


@app.route("/admin/bookings/<int:booking_id>/reschedule", methods=["GET", "POST"])
@role_required("admin")
def admin_reschedule_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    exam = booking.slot.examination

    if request.method == "POST":
        new_slot_id = int(request.form.get("slot_id"))
        new_slot = ExamSlot.query.get_or_404(new_slot_id)

        if new_slot.available_seats <= 0:
            flash("Selected slot has no available seats.", "danger")
            return redirect(url_for("admin_reschedule_booking", booking_id=booking.id))

        # Free previous slot seat
        old_slot = booking.slot
        old_slot.available_seats += 1
        if old_slot.status == "Full":
            old_slot.status = "Available"

        # Assign new slot & decrement seat
        booking.slot_id = new_slot.id
        new_slot.available_seats -= 1
        if new_slot.available_seats == 0:
            new_slot.status = "Full"

        db.session.commit()
        flash(f"Booking #{booking.id} for {booking.student.name} rescheduled successfully.", "success")
        return redirect(url_for("admin_bookings"))

    # Available alternative slots for the same examination
    available_slots = (
        ExamSlot.query.filter(
            ExamSlot.exam_id == exam.id,
            ExamSlot.id != booking.slot_id,
            ExamSlot.available_seats > 0,
            ExamSlot.status != "Cancelled",
        )
        .order_by(ExamSlot.date.asc(), ExamSlot.start_time.asc())
        .all()
    )

    return render_template("admin_reschedule.html", booking=booking, slots=available_slots)


# ---------------------------------------------------------
# Examiner Functionalities
# ---------------------------------------------------------
@app.route("/examiner/dashboard")
@role_required("examiner")
def examiner_dashboard():
    user = current_user()
    slots = ExamSlot.query.filter_by(examiner_id=user.id).order_by(ExamSlot.date.desc()).all()

    # Calculate statistics
    total_slots = len(slots)
    total_students_booked = sum(len([b for b in s.bookings if b.status != "Cancelled"]) for s in slots)

    pending_evals = 0
    completed_evals = 0
    for s in slots:
        for b in s.bookings:
            if b.status == "Booked":
                pending_evals += 1
            elif b.status == "Completed":
                completed_evals += 1

    active_exams_for_slots = Examination.query.filter(
        Examination.status.in_(["Slot Creation", "Booking Open"])
    ).all()

    return render_template(
        "examiner_dashboard.html",
        user=user,
        slots=slots,
        total_slots=total_slots,
        total_students=total_students_booked,
        pending_evals=pending_evals,
        completed_evals=completed_evals,
        active_exams=active_exams_for_slots,
    )


@app.route("/examiner/slots/create", methods=["GET", "POST"])
@role_required("examiner")
def examiner_create_slot():
    user = current_user()
    exams_open_for_creation = [
        e for e in Examination.query.filter_by(status="Slot Creation").all()
        if e.is_slot_creation_active() or e.status == "Slot Creation"
    ]

    if request.method == "POST":
        exam_id = int(request.form.get("exam_id"))
        exam = Examination.query.get_or_404(exam_id)

        # Enforce slot creation period restriction
        if not exam.is_slot_creation_active() and exam.status != "Slot Creation":
            flash("Slot creation window is currently closed for this examination.", "danger")
            return redirect(url_for("examiner_dashboard"))

        slot_date = datetime.strptime(request.form.get("date"), "%Y-%m-%d").date()
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        capacity = int(request.form.get("capacity", 1))

        slot = ExamSlot(
            exam_id=exam.id,
            examiner_id=user.id,
            date=slot_date,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
            available_seats=capacity,
            status="Available",
        )
        db.session.add(slot)
        db.session.commit()
        flash("Examination slot created successfully.", "success")
        return redirect(url_for("examiner_dashboard"))

    return render_template("examiner_slot_form.html", exams=exams_open_for_creation, slot=None)


@app.route("/examiner/slots/<int:slot_id>/edit", methods=["GET", "POST"])
@role_required("examiner")
def examiner_edit_slot(slot_id):
    user = current_user()
    slot = ExamSlot.query.get_or_404(slot_id)

    if slot.examiner_id != user.id:
        flash("Unauthorized access to this slot.", "danger")
        return redirect(url_for("examiner_dashboard"))

    # Slot can only be updated if no bookings exist
    active_bookings = [b for b in slot.bookings if b.status != "Cancelled"]
    if active_bookings:
        flash("Cannot edit a slot that already has student bookings.", "danger")
        return redirect(url_for("examiner_dashboard"))

    if request.method == "POST":
        slot.date = datetime.strptime(request.form.get("date"), "%Y-%m-%d").date()
        slot.start_time = request.form.get("start_time")
        slot.end_time = request.form.get("end_time")
        slot.capacity = int(request.form.get("capacity", 1))
        slot.available_seats = slot.capacity
        db.session.commit()
        flash("Slot updated successfully.", "success")
        return redirect(url_for("examiner_dashboard"))

    exams = [slot.examination]
    return render_template("examiner_slot_form.html", exams=exams, slot=slot)


@app.route("/examiner/slots/<int:slot_id>/delete", methods=["POST"])
@role_required("examiner")
def examiner_delete_slot(slot_id):
    user = current_user()
    slot = ExamSlot.query.get_or_404(slot_id)

    if slot.examiner_id != user.id:
        flash("Unauthorized access to this slot.", "danger")
        return redirect(url_for("examiner_dashboard"))

    active_bookings = [b for b in slot.bookings if b.status != "Cancelled"]
    if active_bookings:
        flash("Cannot delete a slot with confirmed student bookings.", "danger")
        return redirect(url_for("examiner_dashboard"))

    db.session.delete(slot)
    db.session.commit()
    flash("Slot removed successfully.", "info")
    return redirect(url_for("examiner_dashboard"))


@app.route("/examiner/slots/<int:slot_id>/students")
@role_required("examiner")
def examiner_slot_students(slot_id):
    user = current_user()
    slot = ExamSlot.query.get_or_404(slot_id)

    if slot.examiner_id != user.id:
        flash("Unauthorized access to this slot roster.", "danger")
        return redirect(url_for("examiner_dashboard"))

    active_bookings = [b for b in slot.bookings if b.status != "Cancelled"]
    return render_template("examiner_students.html", slot=slot, bookings=active_bookings)


@app.route("/examiner/bookings/<int:booking_id>/evaluate", methods=["GET", "POST"])
@role_required("examiner")
def examiner_evaluate_booking(booking_id):
    user = current_user()
    booking = Booking.query.get_or_404(booking_id)

    # Core constraint: Examiners can only evaluate students booked in their own slots
    if booking.slot.examiner_id != user.id:
        flash("You are not authorized to evaluate this student.", "danger")
        return redirect(url_for("examiner_dashboard"))

    rubrics = booking.slot.examination.rubrics
    existing_evals = {e.rubric_id: e for e in booking.evaluations}

    if request.method == "POST":
        general_remarks = request.form.get("general_remarks", "").strip()

        for rubric in rubrics:
            field_name = f"marks_{rubric.id}"
            marks = float(request.form.get(field_name, 0))
            if marks > rubric.max_marks:
                marks = rubric.max_marks
            elif marks < 0:
                marks = 0

            rubric_remarks = request.form.get(f"remarks_{rubric.id}", "").strip()

            if rubric.id in existing_evals:
                ev = existing_evals[rubric.id]
                ev.marks_awarded = marks
                ev.remarks = rubric_remarks
                ev.evaluated_at = datetime.now(timezone.utc)
            else:
                ev = Evaluation(
                    booking_id=booking.id,
                    rubric_id=rubric.id,
                    marks_awarded=marks,
                    remarks=rubric_remarks,
                )
                db.session.add(ev)

        booking.status = "Completed"
        db.session.commit()
        flash(f"Evaluation submitted successfully for {booking.student.name}.", "success")
        return redirect(url_for("examiner_slot_students", slot_id=booking.slot_id))

    return render_template("examiner_evaluate.html", booking=booking, rubrics=rubrics, existing_evals=existing_evals)


# ---------------------------------------------------------
# Student Functionalities
# ---------------------------------------------------------
@app.route("/student/dashboard")
@role_required("student")
def student_dashboard():
    user = current_user()

    # Active upcoming bookings
    active_bookings = (
        Booking.query.filter_by(student_id=user.id)
        .filter(Booking.status != "Cancelled")
        .order_by(Booking.booking_date.desc())
        .all()
    )

    # Completed bookings with evaluations
    completed_bookings = (
        Booking.query.filter_by(student_id=user.id, status="Completed")
        .order_by(Booking.booking_date.desc())
        .all()
    )

    # Available examinations currently open for booking
    available_exams = Examination.query.filter(
        Examination.status == "Booking Open"
    ).all()

    # Filter out exams already booked by student
    booked_exam_ids = {
        b.slot.exam_id for b in active_bookings if b.status in ["Booked", "Completed"]
    }

    return render_template(
        "student_dashboard.html",
        user=user,
        active_bookings=active_bookings,
        completed_bookings=completed_bookings,
        available_exams=available_exams,
        booked_exam_ids=booked_exam_ids,
    )


@app.route("/student/exams")
@role_required("student")
def student_exams():
    user = current_user()
    name_filter = request.args.get("search", "").strip()
    course_filter = request.args.get("course_id", "")
    type_filter = request.args.get("exam_type", "")

    query = Examination.query.filter(Examination.status.in_(["Booking Open", "Slot Creation", "Completed"]))

    if name_filter:
        query = query.filter(Examination.name.ilike(f"%{name_filter}%"))
    if course_filter and course_filter.isdigit():
        query = query.filter(Examination.course_id == int(course_filter))
    if type_filter:
        query = query.filter(Examination.exam_type == type_filter)

    exams = query.all()
    courses = Course.query.filter_by(status="active").all()

    # Track exams already booked by this student
    active_bookings = Booking.query.filter_by(student_id=user.id).filter(Booking.status != "Cancelled").all()
    booked_exam_ids = {b.slot.exam_id for b in active_bookings}

    return render_template(
        "student_exams.html",
        exams=exams,
        courses=courses,
        search=name_filter,
        course_id=course_filter,
        exam_type=type_filter,
        booked_exam_ids=booked_exam_ids,
    )


@app.route("/student/exams/<int:exam_id>/slots")
@role_required("student")
def student_exam_slots(exam_id):
    user = current_user()
    exam = Examination.query.get_or_404(exam_id)

    # Check if student already has an active booking for this exam
    existing_booking = (
        Booking.query.join(ExamSlot)
        .filter(
            Booking.student_id == user.id,
            ExamSlot.exam_id == exam.id,
            Booking.status.in_(["Booked", "Completed"]),
        )
        .first()
    )

    slots = (
        ExamSlot.query.filter(
            ExamSlot.exam_id == exam.id,
            ExamSlot.status.in_(["Available", "Full"]),
        )
        .order_by(ExamSlot.date.asc(), ExamSlot.start_time.asc())
        .all()
    )

    return render_template(
        "student_exam_slots.html",
        exam=exam,
        slots=slots,
        existing_booking=existing_booking,
    )


@app.route("/student/slots/<int:slot_id>/book", methods=["POST"])
@role_required("student")
def student_book_slot(slot_id):
    user = current_user()
    slot = ExamSlot.query.get_or_404(slot_id)
    exam = slot.examination

    # Rule 1: Booking is allowed ONLY during booking open period
    if not exam.is_booking_active() and exam.status != "Booking Open":
        flash("Booking window is currently closed for this examination.", "danger")
        return redirect(url_for("student_exam_slots", exam_id=exam.id))

    # Rule 2: Prevent duplicate bookings for the same exam by a student
    duplicate = (
        Booking.query.join(ExamSlot)
        .filter(
            Booking.student_id == user.id,
            ExamSlot.exam_id == exam.id,
            Booking.status.in_(["Booked", "Completed"]),
        )
        .first()
    )
    if duplicate:
        flash("You have already booked a slot for this examination.", "warning")
        return redirect(url_for("student_dashboard"))

    # Rule 3: Check seat capacity
    if slot.available_seats <= 0 or slot.status != "Available":
        flash("This slot is already full. Please select another slot.", "danger")
        return redirect(url_for("student_exam_slots", exam_id=exam.id))

    # Create Booking
    booking = Booking(
        student_id=user.id,
        slot_id=slot.id,
        booking_date=datetime.now(timezone.utc),
        status="Booked",
    )
    db.session.add(booking)

    # Decrement slot available seats & update slot status
    slot.available_seats -= 1
    if slot.available_seats == 0:
        slot.status = "Full"

    db.session.commit()
    flash(f"Slot booked successfully for {exam.name} on {slot.date} at {slot.start_time}!", "success")
    return redirect(url_for("student_dashboard"))


@app.route("/student/bookings/<int:booking_id>/cancel", methods=["POST"])
@role_required("student")
def student_cancel_booking(booking_id):
    user = current_user()
    booking = Booking.query.get_or_404(booking_id)

    if booking.student_id != user.id:
        flash("Unauthorized cancellation attempt.", "danger")
        return redirect(url_for("student_dashboard"))

    if booking.status != "Booked":
        flash("This booking cannot be cancelled.", "warning")
        return redirect(url_for("student_dashboard"))

    # Free up seat
    slot = booking.slot
    booking.status = "Cancelled"
    slot.available_seats += 1
    if slot.status == "Full":
        slot.status = "Available"

    db.session.commit()
    flash("Booking cancelled successfully. The examination slot has been released.", "info")
    return redirect(url_for("student_dashboard"))


@app.route("/student/history")
@role_required("student")
def student_history():
    user = current_user()
    bookings = (
        Booking.query.filter_by(student_id=user.id)
        .order_by(Booking.booking_date.desc())
        .all()
    )
    return render_template("student_history.html", bookings=bookings)


@app.route("/student/scorecard/<int:booking_id>")
@role_required("student", "admin")
def student_scorecard(booking_id):
    user = current_user()
    booking = Booking.query.get_or_404(booking_id)

    # Students can view only their own scorecard, Admin can view all
    if user.role == "student" and booking.student_id != user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("student_dashboard"))

    rubrics = booking.slot.examination.rubrics
    evaluations_dict = {e.rubric_id: e for e in booking.evaluations}

    return render_template(
        "student_scorecard.html",
        booking=booking,
        rubrics=rubrics,
        evaluations=evaluations_dict,
    )


# ---------------------------------------------------------
# Run Server
# ---------------------------------------------------------
if __name__ == "__main__":
    import os
    with app.app_context():
        db.create_all()
    # Default to 5001 on macOS to avoid AirPlay Receiver conflict on 5000
    port = int(os.environ.get("PORT", 5001))
    print(f"\n* Starting Examination Management Portal on http://127.0.0.1:{port}")
    app.run(debug=True, port=port)

