from itmostalk.db.bindings import *


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
def get_potok_list():
    potoks = {}
    for potok in Potok.select(lambda x: True):
        potoks.setdefault(potok.discipline, []).append((potok.name, potok.id))
    return potoks


@db_session
def set_potok_list(potoks: dict[str, list[tuple[str, int]]]):
    for discipline, potok_list in potoks.items():
        for potok_name, potok_id in potok_list:
            Potok.get(id=potok_id) or Potok(
                id=potok_id, name=potok_name, discipline=discipline
            )


@db_session
def get_potok_people(potok_id):
    return select(((s.id, s.name) for s in Potok[potok_id].students))[:]


@db_session
def set_potok_people(potok_id, students: list[str]):
    potok = Potok[potok_id]
    for student in students:
        pass

@db_session
def get_potok_schedule(potok_id):
    return select((se.name, se.start, se.end) for se in Potok[potok_id].schedule)[:]


@db_session
def get_student_schedule(student_id):
    student = Student[student_id]
    return select(
        (p.name, se.start, se.end) for p in student.potoks for se in p.schedule
    )[:]
