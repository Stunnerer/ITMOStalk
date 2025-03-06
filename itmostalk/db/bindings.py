from pony.orm import *
from datetime import datetime

db = Database()

class Info(db.Entity):
    name = PrimaryKey(str)
    value = Required(str)

class Student(db.Entity):
    id = PrimaryKey(int)
    name = Required(str)
    groups = Set("Group", table="group_students")
    potoks = Set("Potok", table="potok_students")


class Group(db.Entity):
    id = PrimaryKey(str)
    name = Required(str)
    faculty = Required(str)
    students = Set(Student, table="group_students")


class Potok(db.Entity):
    id = PrimaryKey(int)
    name = Required(str)
    discipline = Required(str)
    students = Set(Student, table="potok_students")
    schedule = Set("ScheduleEntry")


class ScheduleEntry(db.Entity):
    potok = Required(Potok)
    start = Required(datetime)
    end = Required(datetime)
    name = Required(str)
    PrimaryKey(potok, start)

@db_session
def get_student_schedule(student_id):
    student = Student[student_id]
    return select(
        (p.name, se.start, se.end)
        for p in student.potoks
        for se in p.schedule
    )[:]

# Example usage
if __name__ == "__main__":
    # Create database and tables
    db.bind(provider="sqlite", filename=":memory:", create_db=True)
    db.generate_mapping(create_tables=True)
