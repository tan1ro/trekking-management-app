# Trekking Management Application

## Project Overview

The Trekking Management Application is a Flask-based web application that helps manage trekking activities. The system supports three types of users:

* **Admin**
* **Staff**
* **Trekker (User)**

The application allows trek creation and management, trek booking, participant tracking, and trekking history management.


## Installation and Setup

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd trekking_management_app
```

---

### Step 2: Create a Virtual Environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Mac/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3: Install Dependencies

```bash
pip install flask
pip install flask-sqlalchemy
```

Or install all dependencies together:

```bash
pip install flask flask-sqlalchemy
```

---

### Step 4: Initialize the Database

```bash
python create_db.py
```

---

### Step 5: Verify Database Configuration

In `app.py`:

```python
app.config["SECRET_KEY"] = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trekking.db"
```

The application uses SQLite and stores data in `trekking.db`.

---

## Running the Application

Start the Flask server:

```bash
python app.py
```

You should see:

```text
* Running on http://127.0.0.1:5000
```

Open your browser and visit:

```text
http://127.0.0.1:5000/register
```

## Default Admin Credentials

```text
Email: admin@trekking.com
Password: Admin@123
```

Staff Login:
Email: staff@trekking.com
Password: staff@123

Trekker Logins:

Email: trekker1@trekking.com
Password: trekker1@123

Email: trekker2@trekking.com
Password: trekker2@123
---

## Author

Nandeesh Kantli
24F1002499
