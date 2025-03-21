from itmostalk.tui.widgets import (
    TreeSelectionList,
    StepperHeader,
    StepperFooter,
    Schedule,
)
from itmostalk.api import API
from itmostalk.db import functions as cache

import asyncio
import datetime
from textual import work, on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Center
from textual.screen import Screen
from textual.widgets import (
    Button,
    ContentSwitcher,
    Label,
    Input,
    Header,
    Footer,
    Select,
    LoadingIndicator,
)
from textual.reactive import var, reactive
from textual.app import Binding


class LoadingContainer(Container):
    DEFAULT_CSS = """
        LoadingContainer {
            width: 100%;
            height: 100%;
        }
    """

    def compose(self) -> ComposeResult:
        yield LoadingIndicator()


class SelectGroupsContainer(Container):
    def compose(self) -> ComposeResult:
        yield Label(f"Select groups (0/{self.app.MAX_SELECTION})", classes="title")
        yield TreeSelectionList(id="groups")

    @on(TreeSelectionList.SelectionToggled)
    def selection_toggle(self, event: TreeSelectionList.SelectionToggled):
        selected = event.selection_list.selected
        self.log(selected)
        selected = list(filter(lambda x: isinstance(x, str), selected))
        count = len(selected)
        self.query_one(".title", Label).update(
            f"Select groups ({count}/{self.app.MAX_SELECTION})"
        )
        self.screen.ready[1] = False


class SelectPotoksContainer(Container):
    def compose(self) -> ComposeResult:
        yield Label(f"Select potoks (0/{self.app.MAX_SELECTION})", classes="title")
        yield TreeSelectionList(id="potoks")

    @on(TreeSelectionList.SelectionToggled)
    def selection_toggle(self, event: TreeSelectionList.SelectionToggled):
        selected = event.selection_list.selected
        self.log(selected)
        selected = list(filter(lambda x: isinstance(x, str), selected))
        count = len(selected)
        self.query_one(".title", Label).update(
            f"Select potoks ({count}/{self.app.MAX_SELECTION})"
        )
        self.screen.ready[3] = False


class SelectPeopleContainer(Container):
    def compose(self) -> ComposeResult:
        yield Label(f"Select people (0/{self.app.MAX_SELECTION * 5})", classes="title")
        yield TreeSelectionList(id="people")

    @on(TreeSelectionList.SelectionToggled)
    def selection_toggle(self, event: TreeSelectionList.SelectionToggled):
        selected = event.selection_list.selected
        selected = list(filter(lambda x: x > 0, selected))
        count = len(selected)
        self.query_one(".title", Label).update(
            f"Select people ({count}/{self.app.MAX_SELECTION * 5})"
        )


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
                    dict(zip(["start", "end", "subject", "location", "teacher"], pair))
                    for pair in pairs
                ],
            )
            date += datetime.timedelta(days=1)
            pairs = cache.get_student_schedule(students[0][0], date)
            yield Schedule(
                day=date.strftime("%A, %d.%m.%y"),
                entries=[
                    dict(zip(["start", "end", "subject", "location", "teacher"], pair))
                    for pair in pairs
                ],
            )
            date += datetime.timedelta(days=1)
            pairs = cache.get_student_schedule(students[0][0], date)
            yield Schedule(
                day=date.strftime("%A, %d.%m.%y"),
                entries=[
                    dict(zip(["start", "end", "subject", "location", "teacher"], pair))
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
                dict(zip(["start", "end", "subject", "location", "teacher"], pair))
                for pair in pairs
            ]
            date += datetime.timedelta(days=1)

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.title = f"Расписание для студента {event.value}"
        self.student_id = event.value


class SetupScreen(Screen):
    CSS = """
        SetupScreen {
            width: 100%;
            height: 100%;
        }
        .step-arrow {
            margin-left: 10;
            margin-right: 10;
        }
        #contentswitcher { 
            width: 100%;
            height: 100%;
            & > {
                width: 100%;
                height: 100%;
            }
            & > & > TreeSelectionList {
            margin: 1;
            margin-bottom: 3;
            margin-left: 2;
            }
        }
        .title {
            text-align: center;
            width: 100%;
            padding-top: 1;
        }
    """

    current_step = var(-1, init=False)
    steps = ["groups", "people", "potoks", "schedule", "loading"]
    ready = [False] * 4

    def compose(self):
        yield StepperHeader(
            ["группы", "студенты", "потоки", "расписание"], disabled=True
        )
        with ContentSwitcher(id="contentswitcher", initial="loading"):
            yield LoadingContainer(id="loading")
            yield SelectGroupsContainer(id="groups")
            yield SelectPeopleContainer(id="people")
            yield SelectPotoksContainer(id="potoks")
            with Center(id="schedule"):
                yield Label("Расписание построено!")
                yield Button("Посмотреть расписание", id="exit_setup")
        yield StepperFooter()

    @on(Button.Pressed, "#exit_setup")
    async def exit_setup(self, event: Button.Pressed) -> None:
        await self.app.push_screen(MainScreen())

    @work(name="update_groups", exclusive=True)
    async def update_groups(self) -> None:
        api: API = self.app.api
        self.query_one("#status", Label).update("Обновление списка групп...")
        groups = cache.get_group_list()
        if not groups:
            groups = await api.get_group_list()
        self.app.groups = groups
        self.query_one("#groups", TreeSelectionList).set_options(groups)
        self.ready[0] = True
        self.current_step = 0

    @work(name="update_people", exclusive=True)
    async def update_people(self) -> None:
        api: API = self.app.api
        self.query_one("#status", Label).update("Получение студентов...")
        selected = self.query_one("#groups", TreeSelectionList).selected
        selected = list(filter(lambda x: isinstance(x, str), selected))
        if not selected:
            self.current_step = 0
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
                await asyncio.sleep(1)  # rate limit protection
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
        self.ready[1] = True
        self.current_step = 1

    @work(name="update_potoks", exclusive=True)
    async def update_potoks(self) -> None:
        self.query_one("#status", Label).update("Обновление списка потоков...")
        selected = self.query_one("#people", TreeSelectionList).selected
        selected = list(filter(lambda x: x > 0, selected))
        cache.enable_students(selected)
        api: API = self.app.api
        groups = cache.get_potok_list()
        if not groups:
            groups = await api.get_potok_list()
        self.app.potoks = groups
        self.query_one("#potoks", TreeSelectionList).set_options(groups)
        self.ready[2] = True
        self.current_step = 2

    @work(name="build_schedule", exclusive=True)
    async def build_schedule(self) -> None:
        api: API = self.app.api
        potoks_to_fetch = self.query_one("#potoks", TreeSelectionList).selected
        potoks_to_fetch = list(filter(lambda x: x > 0, potoks_to_fetch))
        if not potoks_to_fetch:
            self.current_step = 2
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
                await asyncio.sleep(1)  # rate limit protection

        self.query_one("#status", Label).update(f"Получение расписания (0/{cnt})...")
        for index, potok_id in enumerate(potoks_to_fetch):
            self.query_one("#status", Label).update(
                f"Получение расписания ({index+1}/{cnt})..."
            )
            people = cache.get_potok_schedule(potok_id)
            if not people:
                people = await api.get_potok_schedule(potok_id)
                await asyncio.sleep(1)  # rate limit protection

        self.ready[3] = True
        self.current_step = 3

    def watch_current_step(self, step: int):
        callable = None
        if step > 0 and not self.ready[step]:
            match step:
                case 1:
                    callable = self.update_people
                case 2:
                    callable = self.update_potoks
                case 3:
                    callable = self.build_schedule
            self.set_reactive(SetupScreen.current_step, -1)
            step = -1
        self.query_one(StepperHeader).set_current(step)
        self.query_one(StepperHeader).disabled = step == -1
        self.query_one(ContentSwitcher).current = self.steps[step]
        if step != -1:
            self.query_one("#status", Label).update("")
        if step < 0:
            self.query_one(StepperFooter).query_one("#prev", Button).disabled = True
            self.query_one(StepperFooter).query_one("#next", Button).disabled = True
        elif step == 0:
            self.query_one(StepperFooter).query_one("#prev", Button).disabled = True
            self.query_one(StepperFooter).query_one("#next", Button).disabled = False
        elif step < len(self.steps) - 1:
            self.query_one(StepperFooter).query_one("#prev", Button).disabled = False
            self.query_one(StepperFooter).query_one("#next", Button).disabled = False
        else:
            self.query_one(StepperFooter).query_one("#prev", Button).disabled = False
            self.query_one(StepperFooter).query_one("#next", Button).disabled = True
        if callable:
            callable()

    def on_mount(self):
        self.update_groups()


class LoginScreen(Screen):
    CSS = """
        .centered {
            width: 100%;
            height: 100%;
            align: center middle;
        }
        
        .title {
            text-align: center;
            margin-bottom: 1;
        }

        #error_message {
            color: red;
            text-style: bold;
            text-align: center;
            margin-bottom: 1;
        }

        #login, #password {
            margin-bottom: 1;
        }

        .login-form > * {
            width: 50%;
        }
        
        .button-container {
            align: center top;
            height: auto;
        }

        Button {
            width: 40;
            margin: 10;
            margin-top: 0;
            margin-bottom: 0;
            text-align: center;
        }
    """
    BINDINGS = [Binding("enter", "submit()", "Submit", priority=True)]

    def compose(self) -> ComposeResult:
        with Container(classes="centered"):
            yield Center(
                Label("ITMOStalk", classes="title"),
                Input(id="login", placeholder="Email"),
                Input(id="password", placeholder="Password", password=True),
                Label(id="error_message"),
                classes="login-form",
            )
            yield Horizontal(
                Button("Login", id="login_button"),
                classes="button-container",
            )

    async def action_submit(self) -> None:
        await self.handle_login()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login_button":
            await self.handle_login()

    async def handle_login(self) -> None:
        login = self.query_one("#login", Input).value
        password = self.query_one("#password", Input).value
        button = self.query_one("#login_button", Button)
        button.disabled = True
        button.label = "Logging in..."
        resp = await self.app.api.auth(login, password)
        if resp["success"]:
            self.dismiss()
        else:
            button.label = "Login"
            button.disabled = False
            label = self.query_one("#error_message", Label)
            label.update(resp["message"])
