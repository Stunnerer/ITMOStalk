from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .bindings import Base, Student, Group, Potok, ScheduleEntry, Info
from pathlib import Path
from datetime import date, time
from pytz import timezone


# Initialize SQLAlchemy engine and session
path = Path() / "data" / "cache.db"
engine = create_engine(f"sqlite:///{path.absolute()}")
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def _parse_time(t):
    hour, minute, second = map(int, t.split(":"))
    return time(hour, minute, second, tzinfo=timezone("Europe/Moscow"))

def get_group_list():
    with Session.begin() as session:
        groups = {}
        for group in session.query(Group).all():
            groups.setdefault(group.faculty, []).append((group.name, group.id))
        return groups


def set_group_list(groups: dict):
    with Session.begin() as session:
        for faculty, group_list in groups.items():
            for group_name, group_id in group_list:
                if not session.query(Group).get(group_id):
                    session.add(Group(id=group_id, name=group_name, faculty=faculty))
        session.commit()

def get_group_people(group_id):
    with Session.begin() as session:
        group = session.query(Group).filter(Group.id==group_id).one_or_none()
        if not group:
            return None
        return [(s.id, s.name) for s in list(group.students.order_by(Student.name))]

def enable_students(students: list[int]):
    with Session.begin() as session:
        session.query(Student).filter(Student.id.in_(students)).update({Student.enabled: True})

def disable_students(students: list[int]):
    with Session.begin() as session:
        session.query(Student).filter(Student.id.in_(students)).update({Student.enabled: False})

def get_enabled_students() -> list[tuple[int, str]]:
    with Session.begin() as session:
        return [(s.id, s.name) for s in session.query(Student).filter(Student.enabled).all()]

def get_potok_list() -> dict[str, list[tuple[str, int]]]:
    with Session.begin() as session:
        potoks = {}
        for potok in session.query(Potok).order_by(Potok.discipline).all():
            potoks.setdefault(potok.discipline, []).append((potok.name, potok.id))
        return potoks

def set_potok_list(potoks: dict[str, list[tuple[str, int]]]):
    with Session.begin() as session:
        for discipline, potok_list in potoks.items():
            for potok_name, potok_id in potok_list:
                potok = session.query(Potok).get(potok_id)
                if potok:
                    potok.set(name=potok_name, discipline=discipline)
                else:
                    session.add(Potok(id=potok_id, name=potok_name, discipline=discipline))

def get_potok_people(potok_id):
    with Session.begin() as session:
        potok = session.query(Potok).get(potok_id)
        if not potok:
            return None
        return [(s.id, s.name) for s in list(potok.students.order_by(Student.name))]

def get_potok_schedule(potok_id):
    with Session.begin() as session:
        potok = session.query(Potok).get(potok_id)
        if not potok:
            return None
        return sorted(
            [
                (
                    se.date,
                    _parse_time(se.start),
                    _parse_time(se.end),
                    se.subject,
                    se.location,
                    se.teacher,
                )
                for se in potok.schedule
            ]
        )

def get_student_schedule(student_id, day: date):
    with Session.begin() as session:
        student = session.query(Student).get(student_id)
        if not student:
            return []
        return sorted(
            [
                (
                    _parse_time(se.start),
                    _parse_time(se.end),
                    se.subject,
                    se.location,
                    se.teacher,
                    p.name,
                )
                for p in student.potoks
                for se in p.schedule
                if se.date == day
            ]
        )

def get_groups_with_students() -> dict[str, tuple[str, str, list[str]]]:
    with Session.begin() as session:
        groups_with_students = {}
        for group in session.query(Group).all():
            students = [(s.id, s.name, s.enabled) for s in list(group.students.order_by(Student.name))]
            if students:
                groups_with_students[group.name] = students
        return groups_with_students