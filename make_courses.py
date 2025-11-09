import db_spec
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import csv

engine = create_engine(f"sqlite:///main.db", echo=False, future=True)
with Session(engine) as session:
    courses = []

    with open('courses.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            course = db_spec.Course(
                code=row['code'],
                name=row['name']   
            )

            courses.append(course)
        
    session.add_all(courses)
    session.flush()
    session.commit()

