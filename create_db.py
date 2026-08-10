from app import app
from models import db, User


def setup_database():
    with app.app_context():
        db.create_all()

        admin_email = "admin@trekking.com"
        admin_password = "Admin@123"

        existing_admin = User.query.filter_by(role="admin").first()
        if existing_admin is None:
            db.session.add(
                User(
                    name="Admin",
                    email=admin_email,
                    password=admin_password,
                    role="admin",
                    status="approved",
                )
            )
            db.session.commit()
            print("Default admin account created.")
        else:
            existing_admin.email = admin_email
            existing_admin.password = admin_password
            existing_admin.status = "approved"
            db.session.commit()
            print("Admin account updated.")

        print(f"Login with {admin_email} / {admin_password}")
        print("Database ready.")


if __name__ == "__main__":
    setup_database()
