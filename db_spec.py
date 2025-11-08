# university_sched_sa.py
from pathlib import Path
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, ForeignKey, Table
)
from sqlalchemy.orm import declarative_base, relationship, Session

DB_FILE = Path("main.db")

Base = declarative_base()

# Association table: many-to-many students <-> courses
student_courses = Table(
    "student_courses",
    Base.metadata,
    Column("student_id", ForeignKey("students.id", ondelete="CASCADE"), primary_key=True),
    Column("course_id",  ForeignKey("courses.id",  ondelete="CASCADE"), primary_key=True),
)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    hashed_password = Column(String, nullable=False)

    # A student can attend at most one appointment
    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "appointment_id": self.appointment_id,
            "hashed_password": self.hashed_password,
            "courses": [c.id for c in self.courses]
        }

    # ORM relationships
    courses = relationship("Course", secondary=student_courses, back_populates="students")
    appointment = relationship("Appointment", back_populates="attendees", foreign_keys=[appointment_id])

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    instructor = Column(String)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "instructor": self.instructor,
            "students": [st.id for st in self.students]
        }

    students = relationship("Student", secondary=student_courses, back_populates="courses")

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_student_id = Column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    start_time = Column(String)       # store as ISO-8601 TEXT
    end_time = Column(String)
    additional_info = Column(Text)
    location = Column(String)

    # One-to-many via students.appointment_id
    attendees = relationship("Student", back_populates="appointment", foreign_keys="Student.appointment_id")

    def to_dict(self):
        return {
            "id": self.id,
            "creator_student_id": self.creator_student_id,
            "course_id": self.course_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "additional_info": self.additional_info,
            "location": self.location,
            "attendees": [x.id for x in self.attendees]
        }


    # Convenience relationships
    creator = relationship("Student", foreign_keys=[creator_student_id])
    course = relationship("Course")

from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def build_and_seed(db_path: Path = DB_FILE):
    if db_path.exists():
        db_path.unlink()

    engine = create_engine(f"sqlite:///{db_path}", echo=False, future=True)
    Base.metadata.create_all(engine)

    # Seed with your mock example
    with Session(engine) as session:
        jason = Student(name="Jason Lee", email="jasonlee@umass.edu", hashed_password=pwd_context.hash("password"))
        course = Course(code="POLISCI 273", name="Power", instructor="Andrew March")

        # Link student <-> course (MTM)
        jason.courses.append(course)
        session.add_all([jason, course])
        session.flush()  # get IDs

        appt = Appointment(
            creator_student_id=jason.id,
            course=course,
            start_time="2025-11-07 21:30:00",
            end_time="2025-11-07 22:30:00",
            additional_info="Don't pull up unless you locked!",
            location="W.E.B DuBois Library, Floor 21",
        )
        session.add(appt)
        session.flush()

        # Student attends exactly this one appointment
        jason.appointment = appt

        session.commit()

    print(f"Created {db_path.resolve()}")

if __name__ == "__main__":
    build_and_seed()
