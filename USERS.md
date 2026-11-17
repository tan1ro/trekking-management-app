# Examination Management Portal (EMP) — User Accounts & Viva Scenarios

A simplified, easy-to-remember reference of all user accounts and testing flows for evaluation.

---

## 🔑 1. User Accounts (Quick Reference)

| Role | Name | Email Address | Password | Scenario / Viva Demo Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | System Admin | `admin@emp.iitm.ac.in` | `Admin@123` | **Superuser:** Manage courses, exams, rubrics, approve examiners, reschedule bookings |
| **Examiner** | Dr. Ramesh Sharma | `dr.sharma@emp.iitm.ac.in` | `Examiner@123` | **Approved Examiner:** Create slots, view student roster, submit rubric marks |
| **Examiner** | Prof. Ankit Verma | `prof.verma@emp.iitm.ac.in` | `Examiner@123` | **Pending Approval:** Test the Admin approval workflow |
| **Student** | Nandeesh Kantli | `nandeesh@emp.iitm.ac.in` | `Student@123` | **Candidate:** Browse exams, book a slot live, or cancel a booking |
| **Student** | Aarav Patel | `aarav.patel@emp.iitm.ac.in` | `Student@123` | **Completed Evaluation:** View published scorecard (Score: **38.0 / 40.0 pts**) |

---

## 🧪 2. Quick 3-Step Viva Demonstration

### Step 1: Admin Approval Flow (1 minute)
1. Try logging in as **Prof. Ankit Verma** (`prof.verma@emp.iitm.ac.in` / `Examiner@123`) $\rightarrow$ Portal blocks login and alerts: *"Your examiner account is pending Admin approval"*.
2. Log in as **Admin** (`admin@emp.iitm.ac.in` / `Admin@123`) $\rightarrow$ Go to **Examiners** $\rightarrow$ Click **Approve Access**.
3. Log out and log back in as **Prof. Ankit Verma** $\rightarrow$ Access is immediately granted to the Examiner Dashboard!

### Step 2: Student Slot Booking & Duplicate Prevention (1 minute)
1. Log in as **Nandeesh Kantli** (`nandeesh@emp.iitm.ac.in` / `Student@123`).
2. Go to **Browse & Book Exams** $\rightarrow$ Click **View Available Slots** for *MAD-1 Level 1 Project Viva*.
3. Click **Book Slot** $\rightarrow$ Confirmation message appears, and the booking shows under *Upcoming Bookings*.
4. Try to book another slot for the same exam $\rightarrow$ System blocks duplicate booking.

### Step 3: Examiner Grading & Student Scorecard (1 minute)
1. Log in as **Dr. Ramesh Sharma** (`dr.sharma@emp.iitm.ac.in` / `Examiner@123`).
2. Click **Roster & Evaluate** on your slot $\rightarrow$ Click **Evaluate Candidate**.
3. Enter rubric-wise marks and remarks $\rightarrow$ Submit evaluation.
4. Log in as **Aarav Patel** (`aarav.patel@emp.iitm.ac.in` / `Student@123`) $\rightarrow$ Go to **My History** $\rightarrow$ Click **Scorecard** to view the breakdown.
