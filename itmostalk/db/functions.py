from itmostalk.db.bindings import *
from datetime import date, time, datetime
from pytz import timezone


def _parse_time(t):
    hour, minute, second = map(int, t.split(":"))
    return time(hour, minute, second, tzinfo=timezone("Europe/Moscow"))


@db_session
def get_info():
    return dict(*Info.select(lambda x: True))


@db_session
def get_group_list():
    groups = {}
    for group in Group.select(lambda x: True):
        groups.setdefault(group.faculty, []).append((group.name, group.id))
    return groups


@db_session
def set_group_list(groups: dict[str, list[tuple[str, int]]]):
    for faculty, group_list in groups.items():
        for group_name, group_id in group_list:
            Group.get(id=group_id) or Group(
                id=group_id, name=group_name, faculty=faculty
            )


@db_session
def get_group_people(group_id):
    group = Group.get(id=group_id)
    if not group:
        return None
    return [(s.id, s.name) for s in list(group.students.order_by(Student.name))]


@db_session
def enable_students(students: list[int]):
    for uid in students:
        student = Student.get(id=uid)
        if student:
            student.enabled = True


@db_session
def get_enabled_students():
    return [(s.id, s.name) for s in list(Student.select(lambda x: x.enabled))]


@db_session
def get_potok_list() -> dict[str, list[tuple[str, int]]]:
    potoks = {}
    for potok in Potok.select(lambda _: True).order_by(Potok.discipline):
        potoks.setdefault(potok.discipline, []).append((potok.name, potok.id))
    return potoks


@db_session
def set_potok_list(potoks: dict[str, list[tuple[str, int]]]):
    for discipline, potok_list in potoks.items():
        for potok_name, potok_id in potok_list:
            potok = Potok.get(id=potok_id)
            if potok:
                potok.set(name=potok_name, discipline=discipline)
            else:
                Potok(id=potok_id, name=potok_name, discipline=discipline)


@db_session
def get_potok_people(potok_id):
    potok = Potok.get(id=potok_id)
    if not potok:
        return None
    return [(s.id, s.name) for s in list(potok.students.order_by(Student.name))]


@db_session
def get_potok_schedule(potok_id):
    potok = Potok.get(id=potok_id)
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


@db_session
def get_student_schedule(student_id, day: date):
    student = Student[student_id]
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
