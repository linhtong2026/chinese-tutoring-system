from models import db, User, Tutor, Availability, Session, SessionNote, Feedback
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random
import os

NY_TZ = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

def has_been_seeded():
    return User.query.filter_by(clerk_user_id="clerk_tutor_001").first() is not None

def seed_database():
    if os.getenv("SEED_MOCK_DATA") != "true":
        print("SEED_MOCK_DATA not set to 'true', skipping mock data seeding...")
        return
    
    if has_been_seeded():
        print("Database already seeded, skipping...")
        return
    
    print("Seeding database with mock data...")
    
    tutors_data = [
        {"name": "Anh Nguyen", "email": "anh.nguyen@university.edu", "clerk_id": "clerk_tutor_001", "specialization": "Chinese Literature"},
        {"name": "Linh Tong", "email": "linh.tong@university.edu", "clerk_id": "clerk_tutor_002", "specialization": "Mandarin Speaking"},
        {"name": "Chinh Nguyen", "email": "chinh.nguyen@university.edu", "clerk_id": "clerk_tutor_003", "specialization": "Chinese Grammar"},
    ]
    
    students_data = [
        {"name": "John Smith", "email": "john.smith@student.edu", "clerk_id": "clerk_student_001", "class_name": "Chinese 101"},
        {"name": "Emily Johnson", "email": "emily.j@student.edu", "clerk_id": "clerk_student_002", "class_name": "Chinese 201"},
        {"name": "Michael Brown", "email": "michael.b@student.edu", "clerk_id": "clerk_student_003", "class_name": "Chinese 101"},
        {"name": "Sarah Davis", "email": "sarah.d@student.edu", "clerk_id": "clerk_student_004", "class_name": "Chinese 301"},
        {"name": "David Wilson", "email": "david.w@student.edu", "clerk_id": "clerk_student_005", "class_name": "Chinese 201"},
        {"name": "Jessica Martinez", "email": "jessica.m@student.edu", "clerk_id": "clerk_student_006", "class_name": "Chinese 101"},
        {"name": "Daniel Anderson", "email": "daniel.a@student.edu", "clerk_id": "clerk_student_007", "class_name": "Chinese 301"},
        {"name": "Ashley Thomas", "email": "ashley.t@student.edu", "clerk_id": "clerk_student_008", "class_name": "Chinese 201"},
    ]
    
    professors_data = [
        {"name": "Dr. Robert Lee", "email": "robert.lee@university.edu", "clerk_id": "clerk_prof_001"},
    ]
    
    tutor_users = []
    for tutor_data in tutors_data:
        user = User(
            clerk_user_id=tutor_data["clerk_id"],
            name=tutor_data["name"],
            email=tutor_data["email"],
            role="tutor",
            onboarding_complete=True,
            language_preference="en"
        )
        db.session.add(user)
        db.session.flush()
        
        tutor = Tutor(
            user_id=user.id,
            specialization=tutor_data["specialization"],
            availability_notes="Available for office hours and tutoring sessions"
        )
        db.session.add(tutor)
        db.session.flush()
        tutor_users.append((user, tutor))
    
    student_users = []
    for student_data in students_data:
        user = User(
            clerk_user_id=student_data["clerk_id"],
            name=student_data["name"],
            email=student_data["email"],
            role="student",
            class_name=student_data["class_name"],
            onboarding_complete=True,
            language_preference="en"
        )
        db.session.add(user)
        db.session.flush()
        student_users.append(user)
    
    for prof_data in professors_data:
        user = User(
            clerk_user_id=prof_data["clerk_id"],
            name=prof_data["name"],
            email=prof_data["email"],
            role="professor",
            onboarding_complete=True,
            language_preference="en"
        )
        db.session.add(user)
        db.session.flush()
    
    db.session.commit()
    print(f"Created {len(tutor_users)} tutors, {len(student_users)} students, {len(professors_data)} professor")
    
    now = datetime.now(NY_TZ)
    base_date = datetime(now.year, now.month, now.day, 9, 0, tzinfo=NY_TZ)
    
    availabilities = []
    for tutor_user, tutor in tutor_users:
        for day in range(5):
            start_hour = 9
            for slot in range(3):
                availability = Availability(
                    tutor_id=tutor.id,
                    day_of_week=day,
                    start_time=(base_date + timedelta(hours=start_hour + slot * 2)),
                    end_time=(base_date + timedelta(hours=start_hour + slot * 2 + 2)),
                    session_type=random.choice(["office_hours", "tutoring"]),
                    is_recurring=True
                )
                db.session.add(availability)
                availabilities.append(availability)
    
    db.session.commit()
    print(f"Created {len(availabilities)} recurring availabilities")
    
    sessions = []
    session_notes = []
    feedbacks = []
    
    start_date = now - timedelta(days=90)
    
    courses = ["Chinese 101", "Chinese 201", "Chinese 301"]
    session_types = ["office_hours", "tutoring"]
    attendance_statuses = ["present", "absent", "late"]
    
    note_templates = [
        "Student showed great improvement in pronunciation.",
        "Reviewed grammar concepts. Student needs more practice with tones.",
        "Discussed homework assignment. Student is progressing well.",
        "Worked on character writing. Student is dedicated and focused.",
        "Covered vocabulary for daily conversation. Excellent session.",
        "Student struggled with complex sentence structures but made good effort.",
        "Reviewed for upcoming exam. Student is well-prepared.",
        "Practiced listening comprehension. Student needs more exposure to native speakers.",
    ]
    
    feedback_comments = [
        "Very helpful session! The tutor explained everything clearly.",
        "Great tutor, very patient and knowledgeable.",
        "Learned a lot today. Thank you!",
        "The session was okay but I wish we had more time.",
        "Excellent tutoring session. Highly recommend!",
        "Good session overall. Some concepts were still confusing.",
        "Amazing tutor! Made difficult topics easy to understand.",
        "Really appreciated the extra practice materials.",
    ]
    
    for week in range(12):
        week_date = start_date + timedelta(weeks=week)
        
        for _ in range(random.randint(10, 20)):
            tutor_user, tutor = random.choice(tutor_users)
            student_user = random.choice(student_users)
            
            day_offset = random.randint(0, 6)
            hour = random.randint(9, 17)
            session_date = week_date + timedelta(days=day_offset)
            session_start = datetime(
                session_date.year, session_date.month, session_date.day, 
                hour, 0, tzinfo=NY_TZ
            ).astimezone(UTC)
            session_end = session_start + timedelta(hours=random.choice([1, 2]))
            
            session = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course=random.choice(courses),
                session_type=random.choice(session_types),
                start_time=session_start,
                end_time=session_end,
                status="booked"
            )
            db.session.add(session)
            db.session.flush()
            sessions.append(session)
            
            if session_start < datetime.now(UTC):
                attendance = random.choices(
                    attendance_statuses, 
                    weights=[80, 10, 10]
                )[0]
                
                note = SessionNote(
                    session_id=session.id,
                    tutor_id=tutor_user.id,
                    attendance_status=attendance,
                    notes=random.choice(note_templates),
                    student_feedback=f"Student {'was engaged and participated actively' if attendance == 'present' else 'missed the session' if attendance == 'absent' else 'arrived late but caught up well'}."
                )
                db.session.add(note)
                session_notes.append(note)
                
                if attendance == "present" and random.random() > 0.3:
                    rating = random.choices(
                        [3, 4, 5],
                        weights=[10, 30, 60]
                    )[0]
                    
                    feedback = Feedback(
                        session_id=session.id,
                        student_id=student_user.id,
                        rating=rating,
                        comment=random.choice(feedback_comments)
                    )
                    db.session.add(feedback)
                    feedbacks.append(feedback)
    
    for _ in range(random.randint(15, 25)):
        tutor_user, tutor = random.choice(tutor_users)
        
        future_date = now + timedelta(days=random.randint(1, 14))
        hour = random.randint(9, 17)
        session_start = datetime(
            future_date.year, future_date.month, future_date.day,
            hour, 0, tzinfo=NY_TZ
        ).astimezone(UTC)
        session_end = session_start + timedelta(hours=random.choice([1, 2]))
        
        session = Session(
            tutor_id=tutor_user.id,
            student_id=random.choice(student_users).id if random.random() > 0.3 else None,
            course=random.choice(courses),
            session_type=random.choice(session_types),
            start_time=session_start,
            end_time=session_end,
            status="booked" if random.random() > 0.3 else "available"
        )
        db.session.add(session)
        sessions.append(session)
    
    db.session.commit()
    print(f"Created {len(sessions)} sessions")
    print(f"Created {len(session_notes)} session notes")
    print(f"Created {len(feedbacks)} feedback entries")
    
    print("Database seeding completed successfully!")

