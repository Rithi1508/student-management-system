
import os
import re
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash


# --------------------------------------------------
# 1. LOAD ENVIRONMENT SETTINGS
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if not app.config["SECRET_KEY"] or len(app.config["SECRET_KEY"]) < 32:
    raise RuntimeError(
        "Set a strong SECRET_KEY of at least 32 characters in .env"
    )

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL is missing from your .env file")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Session cookie settings for local development
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.getenv("COOKIE_SECURE", "false").lower() == "true"
)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)

# Allow the local frontend to send session cookies
CORS(
    app,
    resources={
        r"/api/.*": {
            "origins": [
                "http://127.0.0.1:5500",
                "http://localhost:5500",
            ]
        }
    },
    supports_credentials=True,
)

db = SQLAlchemy(app)


# --------------------------------------------------
# 2. STUDENT ACCOUNT MODEL
# --------------------------------------------------


class StudentAccount(db.Model):
    __tablename__ = "student_accounts"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(
        db.String(254),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash = db.Column(db.String(255), nullable=False)

    # Personal profile
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(30), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)

    # Academic profile
    student_number = db.Column(db.String(30), unique=True, nullable=True)
    department = db.Column(db.String(100), nullable=True)
    course = db.Column(db.String(100), nullable=True)
    semester = db.Column(db.Integer, nullable=True)
    college = db.Column(db.String(150), nullable=True)
    academic_year = db.Column(db.String(20), nullable=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )


# --------------------------------------------------
# 3. ANNOUNCEMENTS MODEL
# --------------------------------------------------

class Announcement(db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    published_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )


# --------------------------------------------------
# 4. HOME AND DATABASE HEALTH
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "Student Management System backend is running!"
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    try:
        db.session.execute(text("SELECT 1"))

        return jsonify({
            "success": True,
            "status": "healthy",
            "database": "connected"
        })

    except Exception:
        db.session.rollback()
        app.logger.exception("Database connection check failed")

        return jsonify({
            "success": False,
            "status": "unhealthy",
            "database": "not connected"
        }), 500


# --------------------------------------------------
# 5. STUDENT REGISTRATION
# --------------------------------------------------

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    full_name = str(data.get("full_name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not full_name or len(full_name) > 100:
        return jsonify({
            "success": False,
            "message": "Enter a valid full name."
        }), 400

    if not isinstance(password, str):
        return jsonify({
            "success": False,
            "message": "Enter a valid password."
        }), 400

    if len(email) > 254 or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+", email
    ):
        return jsonify({
            "success": False,
            "message": "Enter a valid email address."
        }), 400

    if len(password) < 12 or len(password) > 128:
        return jsonify({
            "success": False,
            "message": "Password must contain 12 to 128 characters."
        }), 400

    try:
        existing = db.session.execute(
            db.select(StudentAccount).filter_by(email=email)
        ).scalar_one_or_none()

        if existing:
            return jsonify({
                "success": False,
                "message": "An account with this email already exists."
            }), 409

        student = StudentAccount(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
        )

        db.session.add(student)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Student account created successfully."
        }), 201

    except Exception:
        db.session.rollback()
        app.logger.exception("Student registration failed")

        return jsonify({
            "success": False,
            "message": "Unable to create the account."
        }), 500


# --------------------------------------------------
# 6. STUDENT LOGIN
# --------------------------------------------------

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not email or not isinstance(password, str) or not password:
        return jsonify({
            "success": False,
            "message": "Enter your email and password."
        }), 400

    try:
        student = db.session.execute(
            db.select(StudentAccount).filter_by(email=email)
        ).scalar_one_or_none()

        if (
            student is None
            or not check_password_hash(student.password_hash, password)
        ):
            return jsonify({
                "success": False,
                "message": "Invalid email or password."
            }), 401

        # Start a fresh session for the logged-in student
        session.clear()
        session.permanent = True
        session["student_id"] = student.id

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "student": {
                "id": student.id,
                "full_name": student.full_name,
                "email": student.email,
            }
        }), 200

    except Exception:
        app.logger.exception("Student login failed")

        return jsonify({
            "success": False,
            "message": "Unable to complete login."
        }), 500


# --------------------------------------------------
# 7. CHECK CURRENT STUDENT SESSION
# --------------------------------------------------

@app.route("/api/auth/me", methods=["GET"])
def current_student():
    student_id = session.get("student_id")

    if not student_id:
        return jsonify({
            "success": False,
            "message": "Please log in."
        }), 401

    student = db.session.get(StudentAccount, student_id)

    if student is None:
        session.clear()

        return jsonify({
            "success": False,
            "message": "Please log in again."
        }), 401

    return jsonify({
        "success": True,
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "email": student.email,
        }
    }), 200


# --------------------------------------------------
# 7A. GET AND UPDATE STUDENT PROFILE
# --------------------------------------------------

@app.route("/api/profile", methods=["GET"])
def get_profile():
    student_id = session.get("student_id")

    if not student_id:
        return jsonify({
            "success": False,
            "message": "Please log in."
        }), 401

    student = db.session.get(StudentAccount, student_id)

    if student is None:
        session.clear()
        return jsonify({
            "success": False,
            "message": "Please log in again."
        }), 401

    return jsonify({
        "success": True,
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "email": student.email,
            "date_of_birth": (
                student.date_of_birth.isoformat()
                if student.date_of_birth else ""
            ),
            "gender": student.gender or "",
            "phone": student.phone or "",
            "address": student.address or "",
            "student_number": student.student_number or "",
            "department": student.department or "",
            "course": student.course or "",
            "semester": student.semester,
            "college": student.college or "",
            "academic_year": student.academic_year or ""
        }
    }), 200


@app.route("/api/profile", methods=["PUT"])
def update_profile():
    student_id = session.get("student_id")

    if not student_id:
        return jsonify({
            "success": False,
            "message": "Please log in."
        }), 401

    student = db.session.get(StudentAccount, student_id)

    if student is None:
        session.clear()
        return jsonify({
            "success": False,
            "message": "Please log in again."
        }), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid profile data."
        }), 400

    # Update only editable profile fields.
    # Name, email, and password are not changed by this API.
    fields = {
        "gender": 30,
        "phone": 20,
        "address": 5000,
        "department": 100,
        "course": 100,
        "college": 150,
        "academic_year": 20,
        "student_number": 30
    }

    for field, max_length in fields.items():
        if field in data:
            value = data[field]
            if value is not None and not isinstance(value, str):
                return jsonify({
                    "success": False,
                    "message": f"Invalid value for {field}."
                }), 400

            value = (value or "").strip()

            if len(value) > max_length:
                return jsonify({
                    "success": False,
                    "message": f"{field} is too long."
                }), 400

            setattr(student, field, value or None)

    if "date_of_birth" in data:
        dob = data["date_of_birth"]

        if dob in (None, ""):
            student.date_of_birth = None
        else:
            try:
                student.date_of_birth = datetime.strptime(
                    dob, "%Y-%m-%d"
                ).date()
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "message": "Date of birth must use YYYY-MM-DD."
                }), 400

    if "semester" in data:
        semester = data["semester"]

        if semester in (None, ""):
            student.semester = None
        elif (
            isinstance(semester, bool)
            or not isinstance(semester, int)
            or not 1 <= semester <= 12
        ):
            return jsonify({
                "success": False,
                "message": "Semester must be a number from 1 to 12."
            }), 400
        else:
            student.semester = semester

    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Profile updated successfully."
        }), 200

    except Exception:
        db.session.rollback()
        app.logger.exception("Profile update failed")
        return jsonify({
            "success": False,
            "message": "Unable to save the profile."
        }), 500

# --------------------------------------------------
# 8. STUDENT LOGOUT
# --------------------------------------------------

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    }), 200


# --------------------------------------------------
# 9. STUDENT-ONLY ANNOUNCEMENTS
# --------------------------------------------------

@app.route("/api/announcements", methods=["GET"])
def get_announcements():
    student_id = session.get("student_id")

    if not student_id:
        return jsonify({
            "success": False,
            "message": "Please log in to view announcements."
        }), 401

    # Verify that the student account still exists
    student = db.session.get(StudentAccount, student_id)

    if student is None:
        session.clear()

        return jsonify({
            "success": False,
            "message": "Please log in again."
        }), 401

    try:
        announcements = db.session.execute(
            db.select(Announcement).order_by(
                Announcement.published_at.desc(),
                Announcement.id.desc(),
            )
        ).scalars().all()

        return jsonify({
            "success": True,
            "announcements": [
                {
                    "title": item.title,
                    "message": item.message,
                    "published_at": item.published_at.isoformat(),
                }
                for item in announcements
            ]
        }), 200

    except Exception:
        db.session.rollback()
        app.logger.exception("Unable to load announcements")

        return jsonify({
            "success": False,
            "message": "Unable to load announcements."
        }), 500


# --------------------------------------------------
# 10. CREATE MISSING TABLES WITHOUT DROPPING DATA
# --------------------------------------------------


with app.app_context():
    # Create any tables that do not exist yet.
    db.create_all()

    # Find columns already present in the existing MySQL table.
    with db.engine.begin() as connection:
        result = connection.execute(
            text("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'student_accounts'
            """)
        )
        existing_columns = set(result.scalars().all())

        # Add only columns that are missing.
        new_columns = {
            "date_of_birth": "DATE NULL",
            "gender": "VARCHAR(30) NULL",
            "phone": "VARCHAR(20) NULL",
            "address": "TEXT NULL",
            "student_number": "VARCHAR(30) NULL UNIQUE",
            "department": "VARCHAR(100) NULL",
            "course": "VARCHAR(100) NULL",
            "semester": "INT NULL",
            "college": "VARCHAR(150) NULL",
            "academic_year": "VARCHAR(20) NULL",
        }

        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(
                        f"ALTER TABLE student_accounts "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                )
                print(f"Added database column: {column_name}")

    print("Database tables and profile columns are ready.")

# --------------------------------------------------
# 11. START THE DEVELOPMENT SERVER
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
