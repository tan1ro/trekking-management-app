from datetime import date

from flask import Flask, redirect, render_template, request, session

from models import Booking, Trek, User, db

app = Flask(__name__)
app.config["SECRET_KEY"] = "trekking-app-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trekking.db"
db.init_app(app)


def current_role():
    return session.get("role")


def current_user_id():
    return session.get("user_id")


def require_role(*allowed):
    if current_role() not in allowed:
        return redirect("/login")
    return None


def approved_staff_list():
    return User.query.filter_by(role="staff", status="approved").all()


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        selected_role = request.form["role"]
        account_status = "pending" if selected_role == "staff" else "approved"

        db.session.add(
            User(
                name=request.form["name"],
                email=request.form["email"],
                password=request.form["password"],
                role=selected_role,
                status=account_status,
            )
        )
        db.session.commit()
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        account = User.query.filter_by(email=request.form["email"]).first()

        if account is None:
            return "No account found for that email."

        if account.password != request.form["password"]:
            return "Incorrect password."

        if account.status == "inactive":
            return "This account is inactive."

        if account.role == "staff" and account.status != "approved":
            return "Staff approval is still pending."

        session["user_id"] = account.id
        session["role"] = account.role

        destinations = {
            "admin": "/admin/dashboard",
            "staff": "/staff/dashboard",
            "trekker": "/user/dashboard",
        }
        return redirect(destinations.get(account.role, "/login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/admin/dashboard")
def admin_dashboard():
    blocked = require_role("admin")
    if blocked:
        return blocked

    keyword = request.args.get("search")
    matched_users = []
    matched_treks = []

    if keyword:
        matched_users = User.query.filter(User.name.contains(keyword)).all()
        matched_treks = Trek.query.filter(Trek.name.contains(keyword)).all()

    return render_template(
        "admin_dashboard.html",
        total_users=User.query.filter_by(role="trekker").count(),
        total_staff=User.query.filter_by(role="staff").count(),
        pending_staff=User.query.filter_by(role="staff", status="pending").count(),
        total_treks=Trek.query.count(),
        total_bookings=Booking.query.count(),
        staff_members=User.query.filter_by(role="staff").all(),
        treks=Trek.query.all(),
        all_users=User.query.all(),
        user_results=matched_users,
        trek_results=matched_treks,
        search=keyword,
    )


@app.route("/admin/bookings")
def admin_bookings():
    blocked = require_role("admin")
    if blocked:
        return blocked

    return render_template(
        "bookings.html",
        bookings=Booking.query.all(),
        title="All Bookings",
        is_admin=True,
    )


@app.route("/admin/add_trek", methods=["GET", "POST"])
def add_trek():
    blocked = require_role("admin")
    if blocked:
        return blocked

    staff_options = approved_staff_list()

    if request.method == "POST":
        chosen_staff = request.form.get("staff_id")
        trek = Trek(
            name=request.form["name"],
            location=request.form["location"],
            difficulty=request.form["difficulty"],
            duration=int(request.form["duration"]),
            available_slots=int(request.form["slots"]),
            staff_id=int(chosen_staff) if chosen_staff else None,
        )
        db.session.add(trek)
        db.session.commit()
        return redirect("/admin/dashboard")

    return render_template(
        "trek_form.html",
        title="Add Trek",
        button_text="Create Trek",
        trek=None,
        staff_members=staff_options,
    )


@app.route("/edit_trek/<int:trek_id>", methods=["GET", "POST"])
def edit_trek(trek_id):
    blocked = require_role("admin")
    if blocked:
        return blocked

    trek = Trek.query.get_or_404(trek_id)
    staff_options = approved_staff_list()

    if request.method == "POST":
        trek.name = request.form["name"]
        trek.location = request.form["location"]
        trek.difficulty = request.form["difficulty"]
        trek.duration = int(request.form["duration"])
        trek.available_slots = int(request.form["slots"])
        chosen_staff = request.form.get("staff_id")
        trek.staff_id = int(chosen_staff) if chosen_staff else None
        db.session.commit()
        return redirect("/admin/dashboard")

    return render_template(
        "trek_form.html",
        title="Edit Trek",
        button_text="Save Changes",
        trek=trek,
        staff_members=staff_options,
    )


@app.route("/delete_trek/<int:trek_id>")
def delete_trek(trek_id):
    blocked = require_role("admin")
    if blocked:
        return blocked

    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    return redirect("/admin/dashboard")


@app.route("/approve_staff/<int:staff_id>")
def approve_staff(staff_id):
    blocked = require_role("admin")
    if blocked:
        return blocked

    member = User.query.get_or_404(staff_id)
    member.status = "approved"
    db.session.commit()
    return redirect("/admin/dashboard")


@app.route("/toggle_user/<int:user_id>")
def toggle_user(user_id):
    blocked = require_role("admin")
    if blocked:
        return blocked

    person = User.query.get_or_404(user_id)
    person.status = "approved" if person.status == "inactive" else "inactive"
    db.session.commit()
    return redirect("/admin/dashboard")

@app.route("/staff/dashboard")
def staff_dashboard():
    blocked = require_role("staff")
    if blocked:
        return blocked

    assigned = Trek.query.filter_by(staff_id=current_user_id()).all()
    counts = {}
    for item in assigned:
        counts[item.id] = Booking.query.filter(
            Booking.trek_id == item.id,
            Booking.status != "Cancelled",
        ).count()

    return render_template(
        "staff_dashboard.html",
        assigned_treks=assigned,
        participant_counts=counts,
    )


@app.route("/staff/update_trek/<int:trek_id>", methods=["POST"])
def update_trek(trek_id):
    blocked = require_role("staff")
    if blocked:
        return blocked

    trek = Trek.query.get_or_404(trek_id)
    if trek.staff_id != current_user_id():
        return "You cannot update this trek."

    selected_status = request.form["status"]
    trek.status = selected_status
    trek.available_slots = int(request.form["available_slots"])

    if selected_status == "Completed":
        active = Booking.query.filter(
            Booking.trek_id == trek_id,
            Booking.status != "Cancelled",
        ).all()
        for entry in active:
            entry.status = "Completed"

    db.session.commit()
    return redirect("/staff/dashboard")


@app.route("/staff/participants/<int:trek_id>")
def view_participants(trek_id):
    blocked = require_role("staff")
    if blocked:
        return blocked

    trek = Trek.query.get_or_404(trek_id)
    if trek.staff_id != current_user_id():
        return "You cannot view participants for this trek."

    records = Booking.query.filter(
        Booking.trek_id == trek_id,
        Booking.status != "Cancelled",
    ).all()
    return render_template("participants.html", trek=trek, bookings=records)


@app.route("/staff/profile", methods=["GET", "POST"])
def staff_profile():
    blocked = require_role("staff")
    if blocked:
        return blocked

    account = User.query.get(current_user_id())
    if request.method == "POST":
        account.name = request.form["name"]
        account.email = request.form["email"]
        db.session.commit()
        return redirect("/staff/profile")

    return render_template("staff_profile.html", user=account)


@app.route("/user/dashboard")
def user_dashboard():
    blocked = require_role("trekker")
    if blocked:
        return blocked

    trek_query = Trek.query
    name_filter = request.args.get("search")
    level_filter = request.args.get("difficulty")
    place_filter = request.args.get("location")

    if name_filter:
        trek_query = trek_query.filter(Trek.name.contains(name_filter))
    if level_filter:
        trek_query = trek_query.filter(Trek.difficulty == level_filter)
    if place_filter:
        trek_query = trek_query.filter(Trek.location.contains(place_filter))

    return render_template(
        "user_dashboard.html",
        open_treks=trek_query.all(),
        search=name_filter,
        difficulty=level_filter,
        location=place_filter,
    )


@app.route("/book_trek/<int:trek_id>")
def book_trek(trek_id):
    blocked = require_role("trekker")
    if blocked:
        return blocked

    trek = Trek.query.get_or_404(trek_id)
    uid = current_user_id()

    already_booked = Booking.query.filter_by(user_id=uid, trek_id=trek_id).first()
    if already_booked:
        return "You already booked this trek."

    if trek.status != "Open":
        return "Booking is allowed only for Open treks."

    if trek.available_slots <= 0:
        return "No slots left for this trek."

    db.session.add(
        Booking(
            user_id=uid,
            trek_id=trek_id,
            booking_date=date.today(),
            status="Booked",
        )
    )
    trek.available_slots -= 1
    db.session.commit()
    return redirect("/user/dashboard")


@app.route("/my_bookings")
def my_bookings():
    blocked = require_role("trekker")
    if blocked:
        return blocked

    records = Booking.query.filter_by(user_id=current_user_id()).all()
    return render_template(
        "bookings.html",
        bookings=records,
        title="My Bookings",
        is_admin=False,
    )


@app.route("/cancel_booking/<int:booking_id>")
def cancel_booking(booking_id):
    blocked = require_role("trekker")
    if blocked:
        return blocked

    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user_id():
        return "Unauthorized cancellation attempt."

    if booking.status == "Cancelled":
        return redirect("/my_bookings")

    booking.status = "Cancelled"
    booking.trek.available_slots += 1
    db.session.commit()
    return redirect("/my_bookings")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    blocked = require_role("trekker")
    if blocked:
        return blocked

    account = User.query.get(current_user_id())
    if request.method == "POST":
        account.name = request.form["name"]
        account.email = request.form["email"]
        db.session.commit()
        return redirect("/profile")

    return render_template("profile.html", user=account)


if __name__ == "__main__":
    app.run(debug=True)
