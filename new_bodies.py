from pydantic import BaseModel

class NewStudent(BaseModel):
    name: str
    email: str
    password: str

class NewAppointment(BaseModel):
    start_time: str
    end_time: str
    course_id: int 
    location: str
    additional_info: None|str = None

class NewCourse(BaseModel):
    code: str
    name: str
