from datetime import date, datetime, timedelta, timezone
from app import app
from models import Booking, Course, Evaluation, ExamSlot, Examination, Rubric, User, db


def seed_database():
    with app.app_context():
        # Drop and recreate all tables
        db.drop_all()
        db.create_all()

        now = datetime.now()

        # 1. Admin
        admin = User(
            name="System Admin",
            email="admin@emp.iitm.ac.in",
            role="admin",
            status="approved",
            department="Administration",
            contact="9876500001",
        )
        admin.set_password("Admin@123")
        db.session.add(admin)

        # 2. Examiners
        ex1 = User(
            name="Dr. Ramesh Sharma",
            email="dr.sharma@emp.iitm.ac.in",
            role="examiner",
            status="approved",
            department="Computer Science",
            contact="9876511111",
        )
        ex1.set_password("Examiner@123")

        ex2 = User(
            name="Prof. Ankit Verma",
            email="prof.verma@emp.iitm.ac.in",
            role="examiner",
            status="pending",  # Test Admin approval flow
            department="Software Engineering",
            contact="9876522222",
        )
        ex2.set_password("Examiner@123")
        db.session.add_all([ex1, ex2])

        # 3. Students
        st1 = User(
            name="Nandeesh Kantli",
            email="nandeesh@emp.iitm.ac.in",
            role="student",
            status="approved",
            department="Data Science (24F1002499)",
            contact="9876533333",
        )
        st1.set_password("Student@123")

        st2 = User(
            name="Aarav Patel",
            email="aarav.patel@emp.iitm.ac.in",
            role="student",
            status="approved",
            department="Computer Science",
            contact="9876544444",
        )
        st2.set_password("Student@123")
        db.session.add_all([st1, st2])
        db.session.commit()

        # 4. Courses
        c1 = Course(
            code="CS2001",
            name="Modern Application Development I (MAD-1)",
            description="Web app development using Flask, SQLite, and Jinja2.",
            status="active",
        )
        c2 = Course(
            code="CS2002",
            name="Database Management Systems (DBMS)",
            description="Relational database design, normalization, and SQL.",
            status="active",
        )
        db.session.add_all([c1, c2])
        db.session.commit()

        # 5. Examination
        exam1 = Examination(
            course_id=c1.id,
            name="MAD-1 Level 1 Project Viva (T3 2026)",
            exam_type="Viva",
            duration=20,
            max_marks=40.0,
            slot_creation_start=now - timedelta(days=5),
            slot_creation_end=now + timedelta(days=10),
            booking_start=now - timedelta(days=2),
            booking_end=now + timedelta(days=15),
            status="Booking Open",
        )
        exam2 = Examination(
            course_id=c1.id,
            name="MAD-1 Level 2 Comprehensive Demo",
            exam_type="Project Demo",
            duration=30,
            max_marks=60.0,
            status="Slot Creation",
        )
        db.session.add_all([exam1, exam2])
        db.session.commit()

        # 6. Rubrics
        r1 = Rubric(
            exam_id=exam1.id,
            criterion_name="Architecture & Code Walkthrough",
            max_marks=15.0,
            weightage=37.5,
            description="Explanation of MVC routes and models.",
        )
        r2 = Rubric(
            exam_id=exam1.id,
            criterion_name="Live Demonstration & Feature Execution",
            max_marks=15.0,
            weightage=37.5,
            description="Demonstrating booking, approval, and RBAC.",
        )
        r3 = Rubric(
            exam_id=exam1.id,
            criterion_name="Viva Questions & Code Modification",
            max_marks=10.0,
            weightage=25.0,
            description="Answering technical questions and code modifications.",
        )
        db.session.add_all([r1, r2, r3])
        db.session.commit()

        # 7. Examination Slots
        # Open future slot for Nandeesh to book
        slot_open = ExamSlot(
            exam_id=exam1.id,
            examiner_id=ex1.id,
            date=date.today() + timedelta(days=2),
            start_time="10:00",
            end_time="10:20",
            capacity=2,
            available_seats=2,
            status="Available",
        )
        # Completed past slot for Aarav (published scorecard)
        slot_past = ExamSlot(
            exam_id=exam1.id,
            examiner_id=ex1.id,
            date=date.today() - timedelta(days=1),
            start_time="11:00",
            end_time="11:20",
            capacity=1,
            available_seats=0,
            status="Completed",
        )
        db.session.add_all([slot_open, slot_past])
        db.session.commit()

        # 8. Completed Booking & Evaluations (Aarav Patel)
        booking = Booking(
            student_id=st2.id,
            slot_id=slot_past.id,
            booking_date=datetime.now(timezone.utc) - timedelta(days=2),
            status="Completed",
        )
        db.session.add(booking)
        db.session.commit()

        # Rubric evaluations
        db.session.add_all([
            Evaluation(booking_id=booking.id, rubric_id=r1.id, marks_awarded=14.0, remarks="Clear architecture explanation."),
            Evaluation(booking_id=booking.id, rubric_id=r2.id, marks_awarded=15.0, remarks="Smooth live demo of all features."),
            Evaluation(booking_id=booking.id, rubric_id=r3.id, marks_awarded=9.0, remarks="Answered viva questions accurately."),
        ])
        db.session.commit()

        print("\nDatabase seeded successfully!")
        print("Admin:    admin@emp.iitm.ac.in    / Admin@123")
        print("Examiner: dr.sharma@emp.iitm.ac.in / Examiner@123 (Approved)")
        print("Examiner: prof.verma@emp.iitm.ac.in / Examiner@123 (Pending Approval)")
        print("Student:  nandeesh@emp.iitm.ac.in  / Student@123 (Ready to book)")
        print("Student:  aarav.patel@emp.iitm.ac.in / Student@123 (Has Scorecard: 38/40)\n")


if __name__ == "__main__":
    seed_database()
