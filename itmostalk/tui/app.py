from itmostalk.api import API
from itmostalk.tui.screens import MainScreen, LoginScreen

from textual.app import App

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
    api: API = None

    def __init__(self):
        super().__init__()
        self.api = API()

    async def on_mount(self) -> None:
        self.log("qwe")
        await self.api.load_cookies()
        await self.push_screen(MainScreen())
        # if not await self.api.check_auth():
        #     await self.api.get_auth_link()
        #     await self.push_screen(LoginScreen())
