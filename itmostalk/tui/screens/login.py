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
from textual.reactive import var
from textual.app import Binding


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
            await self.app.api.save_cookies()
            self.dismiss()
        else:
            button.label = "Login"
            button.disabled = False
            label = self.query_one("#error_message", Label)
            label.update(resp["message"])
