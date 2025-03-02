from itmostalk.api import API
from itmostalk.tui.screens import MainScreen, LoginScreen

from textual.app import App

class ITMOStalkApp(App):
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
