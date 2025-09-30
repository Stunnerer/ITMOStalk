from itmostalk.api import API
from itmostalk.tui.widgets import Schedule, TreeSelectionList
from itmostalk.db import functions as cache

import asyncio
import datetime
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Container
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Header,
    Footer,
    Select,
    Label,
    ListView,
    ListItem,
    ContentSwitcher,
    Button,
)
from textual.reactive import var

from .setup import SelectPeopleContainer, SelectGroupsContainer, SelectPotoksContainer


class MenuModal(ModalScreen):
    CSS = """
    MenuModal {
        align: center middle;
        & > ContentSwitcher {
            padding: 1;
            min-width: 40%;
            width: auto;
            max-width: 80%;
            height: auto;
            border: tall $primary;
        }
    }
    Label {
        width: 100%;
        text-align: center;
    }
    #menu-container {
        width: 40vw;
        & > ListView {
            background: $surface;
            height: auto;
            & > ListItem {
                padding: 1 2;
            }
        } 
    }
    #people-container,
    #groups-container,
    #potoks-container {
        & > Container {
            width: 100%;
            padding: 1;
            & > Label {
                display: none;
            }
        }
        & > Button {
            width: 100%;
        }
    }
    """

    BINDINGS = [("escape", "go_back()", "Скрыть меню")]

    def action_go_back(self):
        cs = self.query_one(ContentSwitcher)
        if cs.current == "menu-container":
            self.app.pop_screen()
        elif cs.current != "status":
            cs.current = "menu-container"
            self.query_one("#menu-items", ListView).focus()

    async def action_save(self):
        cs = self.query_one(ContentSwitcher)
        match cs.current:
            case "people-container":
                selected = self.query_one("#people", TreeSelectionList).selected
                selected = list(filter(lambda x: x > 0, selected))
                enabled = cache.get_enabled_students()
                enabled = [x[0] for x in enabled]
                cache.disable_students(
                    list(set(enabled) - set(selected))
                )  # disable unchecked
                cache.enable_students(selected)  # enable new checked
                self.screen.dismiss()
                await self.app.screen.recompose()
            case "groups-container":
                selected = self.query_one("#groups", TreeSelectionList).selected
                selected = list(filter(lambda x: isinstance(x, str), selected))
                cs.current = "status"
                self.update_people()
            case "potoks-container":
                selected = self.query_one("#potoks", TreeSelectionList).selected
                selected = list(filter(lambda x: isinstance(x, str), selected))
                cs.current = "status"
                self.build_schedule()
            case _:
                pass

    @work(name="update_people", exclusive=True)
    async def update_people(self) -> None:
        api: API = self.app.api
        self.query_one("#status", Label).update("Получение студентов...")
        selected = self.query_one("#groups", TreeSelectionList).selected
        selected = list(filter(lambda x: isinstance(x, str), selected))
        if not selected:
            return
        groups = {}
        cnt = len(selected)
        for index, group in enumerate(selected):
            self.query_one("#status", Label).update(
                f"Получение студентов ({index + 1}/{cnt})..."
            )
            result = cache.get_group_people(group)
            if not result:
                result = await api.get_people_from_group(group)
            people = []
            for person in result:
                people.append(
                    (
                        f"({person[0]}) {person[1]}",
                        person[0],
                    )
                )
            groups[group.capitalize()] = people
        self.query_one("#people", TreeSelectionList).set_options(groups)
        self.screen.dismiss()
        await self.app.screen.recompose()

    @work(name="build_schedule", exclusive=True)
    async def build_schedule(self) -> None:
        api: API = self.app.api
        potoks_to_fetch = self.query_one("#potoks", TreeSelectionList).selected
        potoks_to_fetch = list(filter(lambda x: x > 0, potoks_to_fetch))
        if not potoks_to_fetch:
            return
        cnt = len(potoks_to_fetch)
        self.query_one("#status", Label).update(f"Построение связей (0/{cnt})...")
        for index, potok_id in enumerate(potoks_to_fetch):
            self.query_one("#status", Label).update(
                f"Построение связей ({index+1}/{cnt})..."
            )
            people = cache.get_potok_people(potok_id)
            if not people:
                people = await api.get_people_from_potok(potok_id)

        self.query_one("#status", Label).update(f"Получение расписания (0/{cnt})...")
        for index, potok_id in enumerate(potoks_to_fetch):
            self.query_one("#status", Label).update(
                f"Получение расписания ({index+1}/{cnt})..."
            )
            people = cache.get_potok_schedule(potok_id)
            if not people:
                people = await api.get_potok_schedule(potok_id)

        self.screen.dismiss()
        await self.app.screen.recompose()

    def compose(self) -> ComposeResult:
        with ContentSwitcher(initial="menu-container"):
            with Container(id="menu-container"):
                yield Label("Menu")
                with ListView(id="menu-items"):
                    yield ListItem(Label("Toggle People"), id="toggle_people")
                    yield ListItem(Label("Add New Groups"), id="add_groups")
                    yield ListItem(Label("Add New Potoks"), id="add_potoks")
                    yield ListItem(Label("Refresh Schedule"), id="refresh")
                    yield ListItem(Label("Re-enter setup"), id="setup")
                    yield ListItem(Label("Close"), id="close")
            with Container(id="people-container"):
                yield Button("Cancel", id="cancel")
                yield SelectPeopleContainer()
                yield Button("Save", id="save")
            with Container(id="groups-container"):
                yield Button("Cancel", id="cancel")
                yield SelectGroupsContainer()
                yield Button("Save", id="save")
            with Container(id="potoks-container"):
                yield Button("Cancel", id="cancel")
                yield SelectPotoksContainer()
                yield Button("Save", id="save")
            yield Label(id="status")

    def on_mount(self):
        self.load_students()
        self.load_groups()
        self.load_potoks()

    @work(exclusive=True)
    async def load_students(self):
        if hasattr(self.app, "group_students"):
            group_students = self.app.group_students
        else:
            self.app.group_students = group_students = cache.get_groups_with_students()
            for group_name, students in group_students.items():
                group_students[group_name] = [(s[1], s[0], s[2]) for s in students]
        people_selection_list = self.query_one("#people", TreeSelectionList)
        people_selection_list.set_options(group_students)

        for student_id, _ in cache.get_enabled_students():
            people_selection_list.select(student_id)

    @work(exclusive=True)
    async def load_groups(self):
        if hasattr(self.app, "groups"):
            groups = self.app.groups
        else:
            self.app.groups = groups = cache.get_group_list()
        group_selection_list = self.query_one("#groups", TreeSelectionList)
        group_selection_list.set_options(groups)

        for faculty, fgroups in groups.items():
            for group_name, group_id in fgroups:
                if group_name in group_students:
                    group_selection_list.select(group_id)

    @work(exclusive=True)
    async def load_potoks(self):
        if hasattr(self.app, "potoks"):
            potoks = self.app.potoks
        else:
            self.app.potoks = potoks = cache.get_potok_list()
        potok_selection_list = self.query_one("#potoks", TreeSelectionList)
        potok_selection_list.set_options(potoks)

    @on(ListView.Selected)
    def handle_selection(self, event: ListView.Selected) -> None:
        item_id = event.item.id
        if item_id == "close":
            self.app.pop_screen()
        elif item_id == "toggle_people":
            self.query_one(ContentSwitcher).current = "people-container"
            self.query_one(SelectPeopleContainer).query_one(TreeSelectionList).focus()
        elif item_id == "add_groups":
            self.query_one(ContentSwitcher).current = "groups-container"
            self.query_one(SelectGroupsContainer).query_one(TreeSelectionList).focus()
        elif item_id == "add_potoks":
            self.query_one(ContentSwitcher).current = "potoks-container"
            self.query_one(SelectPotoksContainer).query_one(TreeSelectionList).focus()
        elif item_id == "refresh":
            self.app.pop_screen()
            # TODO: Add refresh logic here
        elif item_id == "setup":
            from .setup import SetupScreen

            self.app.push_screen(SetupScreen())

    @on(Button.Pressed)
    async def handle_click(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "save":
            await self.action_save()
        elif btn_id == "cancel":
            self.action_go_back()


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
        ("escape", "show_menu()", "Показать меню"),
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

    def action_show_menu(self):
        """Show the modal menu."""
        self.app.push_screen(MenuModal())

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
