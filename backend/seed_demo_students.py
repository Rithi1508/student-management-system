
import secrets

from app import app, db, StudentAccount
from werkzeug.security import generate_password_hash


DEMO_STUDENTS = [
    {
        "full_name": "Renna",
        "email": "renna.demo@example.com",
        "student_number": "STU2026001",
        "date_of_birth": "2005-01-15",
        "gender": "Female",
    },
    {
        "full_name": "Aradhana",
        "email": "aradhana.demo@example.com",
        "student_number": "STU2026002",
        "date_of_birth": "2005-03-20",
        "gender": "Female",
    },
    {
        "full_name": "Saravana",
        "email": "saravana.demo@example.com",
        "student_number": "STU2026003",
        "date_of_birth": "2005-05-12",
        "gender": "Male",
    },
    {
        "full_name": "Jana",
        "email": "jana.demo@example.com",
        "student_number": "STU2026004",
        "date_of_birth": "2005-07-08",
        "gender": "Female",
    },
    {
        "full_name": "Sreethu Nair",
        "email": "sreethu.demo@example.com",
        "student_number": "STU2026005",
        "date_of_birth": "2006-09-25",
        "gender": "Female",
    },
]


with app.app_context():
    db.create_all()

    credentials_to_show = []
    created_count = 0

    for item in DEMO_STUDENTS:
        student = db.session.execute(
            db.select(StudentAccount).filter_by(
                email=item["email"]
            )
        ).scalar_one_or_none()

        if student is not None:
            print(f"Already exists; skipped: {item['email']}")
            continue

        password = secrets.token_urlsafe(16)

        student = StudentAccount(
            full_name=item["full_name"],
            email=item["email"],
            password_hash=generate_password_hash(password),

            student_number=item["student_number"],
            date_of_birth=None,
            gender=item["gender"],

            # Shared class details
            department="Computer Science",
            course="B.Sc. Computer Science",
            semester=4,
            college="Demo College",
            academic_year="2026-2027",

            # No invented personal contact information
            phone=None,
            address=None,
        )

        # Convert the fictional date to a Python date.
        from datetime import date
        student.date_of_birth = date.fromisoformat(
            item["date_of_birth"]
        )

        db.session.add(student)
        credentials_to_show.append(
            (item["full_name"], item["email"], password)
        )
        created_count += 1

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    print(f"\nCreated {created_count} demo account(s).")
    print("Fictional demo credentials — save them securely:")

    for name, email, password in credentials_to_show:
        print(f"\nName: {name}")
        print(f"Email: {email}")
        print(f"Password: {password}")

    print("\nPasswords are generated randomly and stored as hashes.")
