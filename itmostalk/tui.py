from textual.app import App, ComposeResult
from textual.widgets import SelectionList, Button, Label, Input
from textual import on
from textual.screen import Screen
from textual.containers import Center, Horizontal, Vertical, Middle, Container
from typing import Dict, Tuple, List
from textual.binding import Binding
import asyncio


class LoginScreen(Screen):

    BINDINGS = [Binding("enter", "submit()", "Submit", priority=True)]

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Container(
            Center(
                Label("ITMOStalk", classes="title"),
                Input(id="login", placeholder="Login"),
                Input(id="password", placeholder="Password", password=True),
                Label(id="error_message"),
                classes="login-form",
            ),
            Horizontal(
                Button("Login", id="login_button"),
                classes="button-container",
            ),
            classes="centered",
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
        await asyncio.sleep(1)
        if login == "admin" and password == "123":
            self.dismiss()
        else:
            button.label = "Login"
            button.disabled = False
            label = self.query_one("#error_message", Label)
            label.update("Invalid login or password.")


class ITMOStalkApp(App):
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

    def __init__(self):
        super().__init__()

    async def on_mount(self) -> None:
        await self.push_screen(LoginScreen())
