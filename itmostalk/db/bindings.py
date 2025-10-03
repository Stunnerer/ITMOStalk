# Migration to SQLAlchemy
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    Time,
    ForeignKey,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import date, time

Base = declarative_base()

group_students = Table(
    "group_students",
    Base.metadata,
    Column("group", String, ForeignKey("group.id")),
    Column("student", Integer, ForeignKey("student.id")),
)

potok_students = Table(
    "potok_students",
    Base.metadata,
    Column("potok", Integer, ForeignKey("potok.id")),
    Column("student", Integer, ForeignKey("student.id")),
)


class Info(Base):
    __tablename__ = "info"
    name = Column(String, primary_key=True)
    value = Column(String)


class Student(Base):
    __tablename__ = "student"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    enabled = Column(Boolean, default=False)
    groups = relationship(
        "Group", secondary=group_students, back_populates="students", lazy="dynamic"
    )
    potoks = relationship(
        "Potok", secondary=potok_students, back_populates="students", lazy="dynamic"
    )


class Group(Base):
    __tablename__ = "group"
    id = Column(String, primary_key=True)
    name = Column(String)
    faculty = Column(String)
    students = relationship(
        "Student", secondary=group_students, back_populates="groups", lazy="dynamic"
    )


class Potok(Base):
    __tablename__ = "potok"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    discipline = Column(String)
    students = relationship(
        "Student", secondary=potok_students, back_populates="potoks", lazy="dynamic"
    )
    schedule = relationship("ScheduleEntry", back_populates="potok", lazy="dynamic")


class ScheduleEntry(Base):
    __tablename__ = "schedule_entry"
    id = Column(Integer, primary_key=True, autoincrement=True)
    potok_id = Column(Integer, ForeignKey("potok.id"))
    date = Column(Date)
    start = Column(Time)
    end = Column(Time)
    subject = Column(String)
    teacher = Column(String)
    location = Column(String)
    potok = relationship("Potok", back_populates="schedule")
    __table_args__ = (
        UniqueConstraint("potok_id", "date", "start", "end", "subject", "teacher"),
    )
