from itmostalk.tui.widgets import TreeSelectionList, StepperHeader, StepperFooter
from itmostalk.api import API

from textual import work, on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Center
from textual.screen import Screen
from textual.widgets import (
    Button,
    ContentSwitcher,
    Label,
    Input,
    LoadingIndicator,
)
from textual.reactive import var
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
        self.screen.ready[1] = False


class SelectPeopleContainer(Container):
    def compose(self) -> ComposeResult:
        yield Label(f"Select people (0/{self.app.MAX_SELECTION * 5})", classes="title")
        yield TreeSelectionList(id="people")

    @on(TreeSelectionList.SelectionToggled)
    def selection_toggle(self, event: TreeSelectionList.SelectionToggled):
        selected = event.selection_list.selected
        selected = list(filter(lambda x: isinstance(x, str), selected))
        count = len(selected)
        self.query_one(".title", Label).update(
            f"Select groups ({count}/{self.app.MAX_SELECTION})"
        )


class MainScreen(Screen):
    CSS = """
        MainScreen {
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
        yield StepperFooter()

    @work(name="update_groups", exclusive=True, thread=True)
    async def update_groups(self) -> None:
        api: API = self.app.api
        self.query_one("#status", Label).update("Обновление списка групп...")
        groups = await api.get_group_list()
        self.app.groups = groups
        self.query_one("#groups", TreeSelectionList).set_options(groups)
        self.ready[0] = True
        self.current_step = 0

    @work(name="update_people", exclusive=True, thread=True)
    async def update_people(self) -> None:
        api: API = self.app.api
        self.query_one("#status", Label).update("Получение студентов...")
        selected = self.query_one("#groups", TreeSelectionList).selected
        selected = list(filter(lambda x: isinstance(x, str), selected))
        if not selected:
            self.current_step = 0
            return
        groups = {}
        for group in selected:
            result = await api.get_people_from_group(group)
            people = []
            for person in result:
                people.append(
                    (
                        f"({person[0]}) {person[1]}",
                        person[0],
                    )
                )
            groups[group] = people
        self.query_one("#people", TreeSelectionList).set_options(groups)
        self.ready[1] = True
        self.current_step = 1

    @work(name="update_potoks", exclusive=True, thread=True)
    async def update_potoks(self) -> None:
        self.query_one("#status", Label).update("Обновление списка потоков...")
        api: API = self.app.api
        groups = await api.get_potok_list()
        self.app.potoks = groups
        self.query_one("#potoks", TreeSelectionList).set_options(groups)
        self.ready[2] = True
        self.current_step = 2

    def watch_current_step(self, step: int):
        self.query_one(StepperHeader).set_current(step)
        self.query_one(ContentSwitcher).current = self.steps[step]
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
