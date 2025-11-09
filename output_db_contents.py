from sqlalchemy import select, Engine
from sqlalchemy.orm import Session
from db_spec import Base, Student, Course, Appointment  # import your models
from engine import get_engine, start_engine

def appointment_str(a: Appointment):
    return (f"{a.id}: {a.start_time} → {a.end_time}") \
    + f"  Location: {a.location}" \
    + f"  Creator: {a.creator.name if a.creator else None}" \
    + f"  Course: {a.course.code if a.course else None}" \
    + "  Attendees:" + ", ".join(s.name for s in a.attendees)

def student_str(s: Student):
    res = (f"{s.id}: {s.name} ({s.email}) -> appointment_id={s.appointment_id}")
    if s.courses:
        res += "  Courses:" + ", ".join(c.code for c in s.courses)
    return res

def course_str(c: Course):
    return (f"{c.id}: {c.code} - {c.name}") \
    + "  Students:" + ", ".join(s.name for s in c.students)

def print_contents(engine: Engine):
    with Session(engine) as session:
        print("\n=== Students ===")
        for s in session.scalars(select(Student)).all():
            print(student_str(s))

        print("\n=== Courses ===")
        for c in session.scalars(select(Course)).all():
            print(course_str(c))

        print("\n=== Appointments ===")
        for a in session.scalars(select(Appointment)).all():
            print(appointment_str(a))

if __name__ == "__main__":
    start_engine()
    print_contents(get_engine())
