from itmostalk.tui.widgets import Schedule
from itmostalk.db import functions as cache

import datetime
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Header, Footer, Select
from textual.reactive import var


class MainScreen(Screen):
    CSS = """
        MainScreen {
            width: 100%;
            height: 100%;
            & > Horizontal {
                align: center top;
            }
        }
    """

    BINDINGS = [
        ("escape", "toggle_menu()", "Показать меню"),
        ("left", "shift_date(-1)", "Назад"),
        ("right", "shift_date(1)", "Вперед"),
    ]

    current_date = var(datetime.datetime.now().date())
    student_id = var(0)

    def compose(self) -> ComposeResult:
        yield Header()
        students = cache.get_enabled_students()
        options = [(f"({s[0]}) {s[1]}", s[0]) for s in students]
        yield Select(options=options, allow_blank=False, id="students")
        self.current_date = datetime.datetime.now().date()
        self.student_id = students[0][0]
        datetime.timedelta(days=1)
        with Horizontal():
            date = self.current_date - datetime.timedelta(days=1)
            pairs = cache.get_student_schedule(students[0][0], date)
            self.log(pairs)
            yield Schedule(
                day=date.strftime("%A, %d.%m.%y"),
                entries=[
                    dict(
                        zip(
                            ["start", "end", "subject", "location", "teacher", "potok"],
                            pair,
                        )
                    )
                    for pair in pairs
                ],
            )
            date += datetime.timedelta(days=1)
            pairs = cache.get_student_schedule(students[0][0], date)
            yield Schedule(
                day=date.strftime("%A, %d.%m.%y"),
                entries=[
                    dict(
                        zip(
                            ["start", "end", "subject", "location", "teacher", "potok"],
                            pair,
                        )
                    )
                    for pair in pairs
                ],
            )
            date += datetime.timedelta(days=1)
            pairs = cache.get_student_schedule(students[0][0], date)
            yield Schedule(
                day=date.strftime("%A, %d.%m.%y"),
                entries=[
                    dict(
                        zip(
                            ["start", "end", "subject", "location", "teacher", "potok"],
                            pair,
                        )
                    )
                    for pair in pairs
                ],
            )
        yield Footer()

    def action_toggle_menu(self):
        print("it werks")
        pass

    def action_shift_date(self, days):
        self.current_date += datetime.timedelta(days=days)

    def watch_current_date(self, value):
        self.update_schedule()

    def watch_student_id(self, value):
        self.update_schedule()

    def update_schedule(self):
        date = self.current_date - datetime.timedelta(days=1)
        student_id = self.student_id
        for schedule_item in self.query(Schedule):
            print(date.strftime("%A, %d.%m.%y"))
            pairs = cache.get_student_schedule(student_id, date)
            schedule_item.day = date.strftime("%A, %d.%m.%y")
            schedule_item.entries = [
                dict(
                    zip(
                        ["start", "end", "subject", "location", "teacher", "potok"],
                        pair,
                    )
                )
                for pair in pairs
            ]
            date += datetime.timedelta(days=1)

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.title = f"Расписание для студента {event.value}"
        self.student_id = event.value