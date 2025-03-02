from itmostalk.tui.widgets import TreeSelectionList, StepperHeader, StepperFooter
from itmostalk.api import API

from textual import work
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
        yield Label("text")


class SelectGroupsContainer(Container):
    def compose(self) -> ComposeResult:
        yield Label("Select groups", classes="title")
        yield TreeSelectionList(id="groups")


class SelectPeopleContainer(Container):
    def compose(self) -> ComposeResult:
        yield Label("Select people", classes="title")
        yield TreeSelectionList(id="people")


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

    def compose(self):
        yield StepperHeader(["группы", "студенты", "потоки", "расписание"])
        with ContentSwitcher(id="contentswitcher", initial="loading"):
            yield LoadingContainer(id="loading")
            yield SelectGroupsContainer(id="groups")
            yield SelectPeopleContainer(id="people")
        yield StepperFooter()

    @work(name="update_groups")
    async def update_groups(self) -> None:
        api: API = self.app.api
        groups = await api.get_group_list()
        self.app.groups = groups = groups["Бакалавриат"]
        self.query_one("#groups", TreeSelectionList).set_options(groups)
        self.query_one(ContentSwitcher).current = "groups"

    def on_mount(self):
        self.query_one(StepperHeader).set_current(0)
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
