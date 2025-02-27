from itmostalk.tui.widgets import TreeSelectionList, Stepper

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Center
from textual.screen import Screen
from textual.widgets import Button, ContentSwitcher, Footer, Header, Label, Input, LoadingIndicator
from textual.app import Binding


class LoadingContainer(Container):
    def compose(self) -> ComposeResult:
        yield LoadingIndicator()


class SelectGroupsContainer(Container):
    DEFAULT_CSS = """
        .title {
            text-align: center;
            width: 100%;
            margin-top: 10;
        }
    """
    def compose(self) -> ComposeResult:
        yield Label("Select groups", classes="title")
        yield TreeSelectionList({"test": [("qwe", 1), ("asd", 2)]}, id="group-selection-list")

    def validate_selection(self) -> bool:
        q = self.query_one(TreeSelectionList)
        return len(self.query_one(TreeSelectionList).selected) > 0


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
        }
    """

    def compose(self):
        yield StepperHeader(["1", "2", "3"])
        with ContentSwitcher(id="contentswitcher", initial="loading"):
            yield LoadingContainer(id="loading")
            yield SelectGroupsContainer(id="screen1")
        yield StepperFooter()


class LoginScreen(Screen):

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
