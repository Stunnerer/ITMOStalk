from itmostalk.api import API
from itmostalk.tui.screens import SetupScreen, LoginScreen, MainScreen

from textual.app import App


class ITMOStalkApp(App):
    api: API = None
    MAX_SELECTION = 20

    def __init__(self):
        self.api = API()
        super().__init__()

    async def enter_setup(self, _):
        await self.push_screen(SetupScreen())

    async def action_exit_setup(self):
        await self.switch_screen(MainScreen())

    async def on_mount(self) -> None:
        await self.api.load_cookies()
        if not await self.api.check_auth():
            await self.api.get_auth_link()
            await self.push_screen(LoginScreen(), self.enter_setup)
        else:
            await self.push_screen(SetupScreen())
