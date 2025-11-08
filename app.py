from engine import start_engine
start_engine()

from datetime import datetime, timedelta, timezone
from typing import Optional

# app.py
from fastapi import FastAPI, Request, HTTPException, status, Form, Depends
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

import db_utils
from output_db_contents import appointment_str
from pydantic import BaseModel
import uvicorn
import json

app = FastAPI()

@app.get("/", response_class=FileResponse)
async def serve_homepage(request: Request):
    # Serve the HTML file from the static folder
    print(f"Somebody joined at {request.client.host}")
    return FileResponse("static/index.html")

@app.get("/goodbye")
async def goodbye(request: Request):
    client_host = request.client.host
    print(f"🟢 Connection to '/goodbye' from {client_host}")
    return {"message": "Goodbye, world!"}

@app.get("/login")
async def login_page(request: Request):
    return FileResponse("static/login.html")



@app.get("/appointment/{appt_id}")
async def get_appointment_dict(appt_id: int):
    appt_dict = db_utils.get_appointment_dict(appt_id)
    return appt_dict

@app.get("/course/{course_id}")
async def get_course(course_id: int):
    course_dict = db_utils.get_course_dict(course_id)
    return course_dict

@app.get("/student/{student_id}")
async def get_student(student_id: int):
    student_dict = db_utils.get_student_dict(student_id)
    return student_dict

class NewStudent(BaseModel):
    name: str
    email: str
    password: str

@app.post("/create_student/")
async def create_student(body: NewStudent):
    student_id = db_utils.create_student(body.name, body.email, body.password)
    print(student_id)
    return student_id

@app.post("/create_course/")
async def create_course():
    course_id = db_utils.create_course('COMPSCI 240', 'Reasoning Under Uncertainty', "Jack Hughes")
    return course_id

class CoursesForStudent(BaseModel):
    student_id: int
    course_ids: list[int]

@app.post('/set_courses_for_student/')
async def set_courses_for_student(body: CoursesForStudent):
    db_utils.set_courses_for_student(body.student_id, body.course_ids)

class AppointmentBody(BaseModel):
    creator_student_id: int
    start_time: str
    end_time: str
    course_id: int 
    additional_info: None|str = None
    location: None|str = None
    add_creator_as_attendee: bool = True

@app.post('/create_appointment/')
async def create_appointment(body: AppointmentBody):
    aid = db_utils.create_appointment(
        body.creator_student_id,
        body.course_id,
        body.start_time,
        body.end_time,
        body.additional_info,
        body.location,
        body.add_creator_as_attendee,
    )
    return aid

@app.post('/add_attendee_to_appointment/')
async def add_attendee_to_appointment(appt_id: int, st_id: int):
    db_utils.add_attendee_to_appointment(appt_id, st_id)

@app.post('/extend_appointment_end_time/')
async def extend_appointment_end_time(appt_id: int, new_end_time: str):
    db_utils.extend_appointment_end_time(appt_id, new_end_time)

@app.post('/end_appointment/{appt_id}')
async def end_appointment(appt_id: int):
    db_utils.end_appointment(appt_id)

class Courses(BaseModel):
    course_ids: list[int]

@app.get('/get_appointments_for_course/{id}')
async def get_appointments_for_courses(id: int):
    appointments = db_utils.get_appointments_for_course(id)
    return json.dumps(appointments)

@app.get('/get_courses_for_student/{id}')
async def get_courses_for_student(id: int):
    courses = db_utils.get_courses_for_student(id)
    return json.dumps(courses)

@app.get('/get_attending_students/{aid}')
async def get_attending_students(aid: int):
    try:
        attendees = db_utils.get_attending_students(aid)
        return json.dumps(attendees)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"No appointment with ID {aid}")

### LOGIN MECHANISM ###

# -------------------------
# Settings (use env vars in real apps)
# -------------------------
SECRET_KEY = "change-me-very-secret"         # os.environ["SECRET_KEY"]
REFRESH_SECRET_KEY = "change-me-refresh"     # os.environ["REFRESH_SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenPayload(BaseModel):
    sub: str
    type: str
    exp: int

# -------------------------
# Helpers
# -------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_student(email: str, password: str):
    student_dict = db_utils.get_student_from_email(email)
    verified = verify_password(password, student_dict['hashed_password'])
    if not verified:
        return None
    return student_dict

def _create_token(subject: str, token_type: str, expires_delta: timedelta, key: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,         # who
        "type": token_type,     # "access" or "refresh"
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, key, algorithm=ALGORITHM)

def create_access_token(subject: str) -> str:
    return _create_token(
        subject, "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), SECRET_KEY
    )

def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject, "refresh", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), REFRESH_SECRET_KEY
    )

def decode_token(token: str, expected_type: str) -> TokenPayload:
    try:
        key = SECRET_KEY if expected_type == "access" else REFRESH_SECRET_KEY
        payload = jwt.decode(token, key, algorithms=[ALGORITHM])
        data = TokenPayload(**payload)
        if data.type != expected_type:
            raise JWTError("Wrong token type")
        return data
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Accepts form fields: username, password (per OAuth2 spec).
    """
    user = authenticate_student(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password... FUCK OFF")

    access = create_access_token(user['email'])
    refresh = create_refresh_token(user['email'])
    return Token(
        access_token=access,
        refresh_token=refresh,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

@app.post("/auth/refresh", response_model=Token)
def refresh(access_token: Optional[str] = Form(default=None),
            refresh_token: str = Form(...)):
    """
    Exchange a valid refresh token for a new access token.
    Optionally accept the old access token for logging / checks.
    """
    payload = decode_token(refresh_token, expected_type="refresh")
    # Optional: check token rotation / jti blacklist here
    new_access = create_access_token(payload.sub)
    new_refresh = create_refresh_token(payload.sub)  # rotate; or return the same if you prefer
    return Token(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # expects Bearer token

# Dependency used by protected routes
def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_token(token, expected_type="access")
    email = payload.sub
    student_dict = db_utils.get_student_from_email(email)
    if not student_dict or student_dict.get("disabled", False):
        raise HTTPException(status_code=401, detail="Inactive or missing user")
    return {k: v for k, v in student_dict.items() if k != 'hashed_password'}

# Example of an endpoint locked by login
@app.get("/me")
def read_me(current_user: dict = Depends(get_current_user)):
    return current_user

import socket

if __name__ == "__main__":

    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Join up in {ip_address}")

    uvicorn.run("app:app", host="0.0.0.0", port=80, log_level="info", reload=True)

    print("Bye bye!")