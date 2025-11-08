from db_utils import (
    create_student, create_course, set_courses_for_student,
    create_appointment, add_attendee_to_appointment,
    extend_appointment_end_time, end_appointment,
    get_appointments_for_courses, get_courses_for_student,
    get_attending_students,
    get_engine
)

from output_db_contents import print_contents

appts = get_appointments_for_courses([2])
courses = get_courses_for_student(student_id=1)
attendees = get_attending_students(appointment_id=1)

for x in attendees:
    print(x)

engine = get_engine()
print_contents(engine)

print(appts)