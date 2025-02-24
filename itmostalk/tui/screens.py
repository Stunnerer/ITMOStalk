from itmostalk.tui.widgets import TreeSelectionList

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Center
from textual.screen import Screen
from textual.widgets import Button, ContentSwitcher, Footer, Header, Label, Input
from textual.app import Binding


class SelectGroupsScreen(Container):

    def compose(self) -> ComposeResult:
        yield TreeSelectionList({"test": [("qwe", 1), ("asd", 2)]}, id="selection-list")
        yield Button("Next", id="next_btn")

    def validate_selection(self) -> bool:
        return len(self.query_one(TreeSelectionList).selected) > 0


class MainScreen(Screen):
    CSS = """
        #progress-steps {
            align: center top;
            background: #f00;
        }
        .step-arrow {
            margin-left: 10;
            margin-right: 10;
        }
    """

    def compose(self):
        with Header():
            with Horizontal(id="progress-steps"):
                yield Label("1", classes="first step", id="step1")
                yield Label("->", classes="step-arrow")
                yield Label("2", classes="step", id="step2")
                yield Label("->", classes="step-arrow")
                yield Label("3", classes="step", id="step3")
                yield Label("->", classes="step-arrow")
                yield Label("4", classes="step", id="step4")
        with ContentSwitcher(id="contentswitcher", initial="screen1"):
            yield SelectGroupsScreen(id="screen1")
        yield Footer()

        with Header():
            with Horizontal(id="progress-steps"):
                yield Label("1", classes="first step", id="step1")
                yield Label("->", classes="step-arrow")
                yield Label("2", classes="step", id="step2")
                yield Label("->", classes="step-arrow")
                yield Label("3", classes="step", id="step3")
                yield Label("->", classes="step-arrow")
                yield Label("4", classes="step", id="step4")
        with ContentSwitcher(id="contentswitcher", initial="screen1"):
            yield SelectGroupsScreen(id="screen1")
        yield Footer()


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
