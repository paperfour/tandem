
from contextlib import contextmanager
from typing import Iterable, Sequence, Optional
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db_spec import Student, Course, Appointment
from engine import get_engine

engine = get_engine()

from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

@contextmanager
def session_scope():
    """Transactional scope."""
    with Session(engine) as s:
        try:
            yield s
            s.commit()
        except:
            s.rollback()
            raise

# --- Helpers ---
def _get_student(s: Session, student_id: int) -> Student:
    st = s.get(Student, student_id)
    if not st:
        raise ValueError(f"Student {student_id} not found.")
    return st

def _get_course(s: Session, course_id: int) -> Course:
    c = s.get(Course, course_id)
    if not c:
        raise ValueError(f"Course {course_id} not found.")
    return c

def _get_appointment(s: Session, appt_id: int) -> Appointment:
    a = s.get(Appointment, appt_id)
    if not a:
        raise ValueError(f"Appointment {appt_id} not found.")
    return a

# --- Utilities ---
def get_appointment_dict(appt_id: int) -> dict:
    with session_scope() as s:
        a = _get_appointment(s, appt_id)
        return a.to_dict()
    
def get_student_appointment(student_id: int) -> dict | None:
    with session_scope() as s:
        
        appt_id = get_student_dict(student_id)["appointment_id"]
        try:
            appt_dict = get_appointment_dict(appt_id)
        except:
            _get_student(s, student_id).appointment_id = None
            return None

        return appt_dict

def get_student_dict(student_id: int) -> dict:
    with session_scope() as s:
        st = _get_student(s, student_id)
        return st.to_dict()

def get_course_dict(course_id: int) -> dict:
    with session_scope() as s:
        c = _get_course(s, course_id)
        return c.to_dict()

def create_student(name: str, email: str, password: str) -> int:
    """Create a Student (name, email). Returns student id."""
    with session_scope() as s:
        st = Student(name=name.strip(), 
                     email=email.strip(),
                     hashed_password=pwd_context.hash(password))
        s.add(st)
        s.flush()
        return st.id 

def create_course(code: str, name: str, instructor: Optional[str] = None) -> int:
    """Create a Course. Returns course id."""
    with session_scope() as s:
        c = Course(code=code.strip(), name=name.strip(), instructor=(instructor or None))
        s.add(c)
        s.flush()
        return c.id

def set_courses_for_student(student_id: int, course_ids: Sequence[int]) -> None:
    """
    Set the student's enrolled courses to exactly 'course_ids'
    (adds missing, removes extras).
    """
    with session_scope() as s:
        st = _get_student(s, student_id)
        # Load current set
        current_ids = {c.id for c in st.courses}
        target_ids = set(course_ids)

        # Remove extras
        for c in list(st.courses):
            if c.id not in target_ids:
                st.courses.remove(c)

        # Add missing
        missing = target_ids - current_ids
        if missing:
            to_add = s.scalars(select(Course).where(Course.id.in_(missing))).all()
            if len(to_add) != len(missing):
                found = {c.id for c in to_add}
                missing_report = sorted(missing - found)
                raise ValueError(f"Courses not found: {missing_report}")
            st.courses.extend(to_add)

def create_appointment(
    creator_student_id: int,
    course_id: int,
    start_time: str,
    end_time: str,
    location: str,
    additional_info: Optional[str],
) -> int:
    """
    Create an appointment. Optionally adds the creator as attendee
    (enforces one-appointment-per-student).
    Returns appointment id.
    """
    with session_scope() as s:
        
        creator = _get_student(s, creator_student_id)
        course = _get_course(s, course_id) if course_id is not None else None

        appt = Appointment(
            creator_student_id=creator.id,
            course=course,
            start_time=start_time,
            end_time=end_time,
            location=location,
            additional_info=additional_info,
        )
        s.add(appt)     
        s.flush()  # assign appt.id

        if creator.appointment_id and creator.appointment_id != appt.id:
            # print('FUCL')
            raise ValueError(f"Student {creator.id} already attends appointment {creator.appointment_id}.")
        creator.appointment_id = appt.id

        return appt.id

def add_attendee_to_appointment(appointment_id: int, student_id: int) -> None:
    """Assign the student to attend the given appointment. Enforces at most one appointment per student."""
    with session_scope() as s:
        appt = _get_course(s, appointment_id)
        st = _get_student(s, student_id)

        if st.appointment_id and st.appointment_id != appt.id:
            raise ValueError(f"Student {student_id} already attends appointment {st.appointment_id}.")
        st.appointment_id = appt.id  # links via FK

def remove_attendee_from_appointment(appointment_id: int, student_id: int) -> None:
    """Assign the student to attend the given appointment. Enforces at most one appointment per student."""
    with session_scope() as s:
        appt = _get_course(s, appointment_id)
        st = _get_student(s, student_id)

        if st.appointment_id and st.appointment_id != appt.id:
            raise ValueError(f"Student {student_id} doesn't seem to be attending {st.appointment_id}.")
        st.appointment_id = None  # links via FK

def edit_appointment(
    appointment_id: int,     
    start_time: str,
    end_time: str,
    location: str,
    additional_info: Optional[str],
) -> None:
    """Set a later end_time for the appointment."""
    with session_scope() as s:
        appt = _get_appointment(s, appointment_id)
        appt.start_time = start_time
        appt.end_time = end_time
        appt.additional_info = additional_info
        appt.location = location

def end_appointment(appointment_id: int) -> None:
    """
    End the appointment early by deleting it.
    All attending students are detached (appointment_id = NULL) before deletion.
    """
    with session_scope() as s:
        appt = _get_appointment(s, appointment_id)
    
        # Detach attendees for safety (ORM-level), regardless of ON DELETE SET NULL
        for st in list(appt.attendees):
            print(st)
            st.appointment_id = None

        s.delete(appt)
        # commit handled by context manager
# --- Additional read utilities ---

def clear_hanging_appointments():
    with session_scope() as s:
        # appt = _get_appointment(s, aid)
        appts = s.query(Appointment).all()
        for appt in appts:
            creator = _get_student(s, appt.creator.id)

            if creator.appointment_id != appt.id:
                s.delete(appt)

from sqlalchemy import select, func

def get_appointments_for_course(course_id: int) -> list[dict]:
    """
    Return appointments linked to any course in course_ids.
    [
      {id, course_id, creator_student_id, start_time, end_time, location, additional_info}
    ]
    """
    with session_scope() as s:
        stmt = (
            select(Appointment)
            .where(Appointment.course_id == course_id)
            .order_by(Appointment.start_time)
        )
        rows = s.scalars(stmt).all()
        return [a.to_dict() for a in rows]
    

def get_courses_for_student(student_id: int) -> list[dict]:
    """
    Return all courses a student is enrolled in.
    """
    with session_scope() as s:
        st = _get_student(s, student_id)
        # Ensure collection is loaded in-session
        return [c.to_dict() for c in st.courses]

def get_attending_students(appointment_id: int) -> list[dict]:
    """
    Return all students attending an appointment.
    """
    with session_scope() as s:
        appt = _get_appointment(s, appointment_id)
        # appt.attendees is the ORM one-to-many via Student.appointment_id
        return [st.to_dict() for st in appt.attendees]
    
def get_creator(appointment_id: int) -> list[dict]:
    """
    Return the creator of an appointment.
    """
    with session_scope() as s:
        appt = _get_appointment(s, appointment_id)
        return appt.creator.to_dict()

def get_student_from_email(email_to_search: str):
    with session_scope() as s:
        st = s.query(Student).filter(Student.email == email_to_search).first()

        if st is None: return None

        dct = st.to_dict()
        return dct
    

# DEBUG ONLY
def get_all_students():
    with session_scope() as s:
        return [stud.to_dict() for stud in s.query(Student).all()]

def get_all_appointments():
    with session_scope() as s:
        return [appt.to_dict() for appt in s.query(Appointment).all()]
    
def get_all_courses():
    with session_scope() as s:
        return [course.to_dict() for course in s.query(Course).all()]
