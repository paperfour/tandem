from engine import start_engine
start_engine()

from datetime import datetime, timedelta, timezone
from typing import Optional

# app.py
from fastapi import FastAPI, Request, HTTPException, status, Form, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pathlib import Path
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from passlib.context import CryptContext

import db_utils

from pydantic import BaseModel
from new_bodies import NewStudent, NewAppointment, NewCourse
import uvicorn
import json

app = FastAPI()

### LOGIN MECHANISM =======================================================================

# Settings (use env vars in real apps)
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

# Helpers
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

# Requests
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

### GETTERS/SETTERS - USER ====================================================

# Dependency used by protected routes
def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_token(token, expected_type="access")
    email = payload.sub
    student_dict = db_utils.get_student_from_email(email)
    if not student_dict or student_dict.get("disabled", False):
        raise HTTPException(status_code=401, detail="Inactive or missing user")
    return {k: v for k, v in student_dict.items() if k != 'hashed_password'}

@app.get('/current_user/')
async def get_cur_user_endpoint(current_user: dict = Depends(get_current_user)):
    return current_user

# COURSES
class CoursesForStudent(BaseModel):
    course_ids: list[int]

@app.post('/set_courses_for_student/')
async def set_courses_for_student(body: CoursesForStudent, current_user: dict = Depends(get_current_user)):
    st_id = current_user['id']
    db_utils.set_courses_for_student(st_id, body.course_ids)

@app.post('/add_course_for_student/')
async def add_course_for_student(course_id: int, current_user: dict = Depends(get_current_user)):
    st_id = current_user['id']
    cur_course_ids = [c['id'] for c in db_utils.get_courses_for_student(st_id)]
    
    if course_id in cur_course_ids:
        raise HTTPException(status_code=403, detail="You're already in the course you're trying to join.")
    
    cur_course_ids.append(course_id)
    db_utils.set_courses_for_student(st_id, cur_course_ids)

@app.post('/remove_course_for_student/')
async def remove_course_for_student(course_id: int, current_user: dict = Depends(get_current_user)):
    st_id = current_user['id']
    cur_course_ids = [c['id'] for c in db_utils.get_courses_for_student(st_id)]
    
    if course_id not in cur_course_ids:
        raise HTTPException(status_code=403, detail="You're not in the course you're trying to leave.")
    
    cur_course_ids.remove(course_id)
    db_utils.set_courses_for_student(st_id, cur_course_ids)

@app.get('/get_courses_for_student/')
async def get_courses_for_student(current_user: dict = Depends(get_current_user)):
    st_id = current_user['id']
    courses = db_utils.get_courses_for_student(st_id)
    return (courses)

# APPOINTMENTS
@app.post('/create_appointment/')
async def create_appointment(body: NewAppointment, current_user: dict = Depends(get_current_user)):
    try:
        creator_id = current_user['id']
        aid = db_utils.create_appointment(
            creator_id,
            body.course_id,
            body.start_time,
            body.end_time,
            body.location,
            body.additional_info,
        )
        return aid
    except:
        raise HTTPException(403, "You are the owner of an existing appointment.")

@app.post('/join_appointment/{appt_id}')
async def join_appointment(appt_id: int, current_user: dict = Depends(get_current_user)):
    try:
        st_id = current_user['id']
        db_utils.add_attendee_to_appointment(appt_id, st_id)
    except ValueError:
        raise HTTPException(403, detail="You are the owner of an existing appointment.")

@app.post('/leave_appointment/')
async def leave_appointment(current_user: dict = Depends(get_current_user)):
    st_id = current_user['id']
    appt_dict = db_utils.get_student_appointment(st_id)

    if appt_dict['creator_student_id'] == st_id:
        raise HTTPException(status_code=403, detail="You can't leave an appointment you created. End the appointment instead")
    db_utils.remove_attendee_from_appointment(appt_dict['id'], st_id)
    
@app.post('/edit_appointment/')
async def edit_appointment(body: NewAppointment, current_user: dict = Depends(get_current_user)):
    st_id = current_user['id']
    appt_dict = db_utils.get_student_appointment(st_id)

    if st_id != appt_dict['creator_student_id']:
        raise HTTPException(status_code=403, detail="You are not the owner of this appointment")
    
    db_utils.edit_appointment(
        appt_dict['id'], 
        body.start_time,
        body.end_time,
        body.location,
        body.additional_info,
    )

@app.post('/end_appointment/')
async def end_appointment(current_user: dict = Depends(get_current_user)):
    st_id = current_user['id']
    appt_dict = db_utils.get_student_appointment(st_id)

    if appt_dict['creator_student_id'] != st_id:
        raise HTTPException(status_code=403, detail="You do not own this appointment")

    db_utils.end_appointment(appt_dict['id'])



@app.get('/feed')
async def get_student_feed(current_user: dict = Depends(get_current_user)):
    db_utils.clear_hanging_appointments()

    st_id = current_user['id']

    student_courses = db_utils.get_courses_for_student(st_id)
    
    appointments = []
    for c in student_courses:
        c_id = c['id']
        appointments += db_utils.get_appointments_for_course(c_id)
    
    return appointments


#  ===========================================================================

BASE_DIR  = Path(__file__).parent.resolve()
HTML_DIR  = BASE_DIR / "html"
CSS_DIR   = BASE_DIR / "css"
JS_DIR    = BASE_DIR / "js"
IMG_DIR    = BASE_DIR / "IMG"

app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")
app.mount("/js",  StaticFiles(directory=JS_DIR),  name="js")
app.mount("/html",  StaticFiles(directory=HTML_DIR), name="html")
app.mount("/IMG",  StaticFiles(directory=IMG_DIR), name="IMG")

@app.get("/")
async def root():
    index = HTML_DIR / "index.html"
    if index.exists():
        return FileResponse(index, media_type="text/html; charset=utf-8")
    raise HTTPException(404, detail="/html/index.html not found")

@app.get("/login", response_class=FileResponse)
async def login_page(request: Request):
    return FileResponse("static/login.html")

@app.get("/tests", response_class=FileResponse)
async def login_page(request: Request):
    return FileResponse("static/tests.html")

@app.get("/appointment/{appt_id}")
async def get_appointment_dict(appt_id: int):
    appt_dict = db_utils.get_appointment_dict(appt_id)
    return appt_dict

@app.get("/course/{course_id}")
async def get_course_dict(course_id: int):
    course_dict = db_utils.get_course_dict(course_id)
    return course_dict

# * Not Authed
@app.post("/create_student/")
async def create_student(body: NewStudent):
    student_id = db_utils.create_student(body.name, body.email, body.password)
    print(student_id)
    return student_id

@app.get('/get_appointments_for_course/{id}')
async def get_appointments_for_courses(id: int):
    appointments = db_utils.get_appointments_for_course(id)
    return (appointments)

@app.get('/get_attending_students/{aid}')
async def get_attending_students(aid: int):
    try:
        attendees = db_utils.get_attending_students(aid)
        return (attendees)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"No appointment with ID {aid}")
    
@app.get('/get_creator/{aid}')
async def get_creator(aid: int):
    try:
        creator = db_utils.get_creator(aid)
        return (creator)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"No appointment with ID {aid}")

@app.get('/all_courses')
async def all_courses():
    return [{
        k: v for k, v in c.items() if k != 'students'
    } for c in db_utils.get_all_courses()]

@app.get("/debug/db_all")
async def debug_db_all():
    """
    Returns a snapshot of all major tables.
    This is for testing only — remove or protect it in production.
    """
    try:
        students = db_utils.get_all_students()
    except Exception:
        students = "Unavailable"

    try:
        courses = db_utils.get_all_courses()
    except Exception:
        courses = "Unavailable"

    try:
        appointments = db_utils.get_all_appointments()
    except Exception:
        appointments = "Unavailable"

    return {
        "students": students,
        "appointments": appointments,
        "courses": courses
    }


import socket
if __name__ == "__main__":

    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"Join up in {ip_address}")

    uvicorn.run("app:app", host="0.0.0.0", port=80, log_level="info", reload=True)

    print("Bye bye!")