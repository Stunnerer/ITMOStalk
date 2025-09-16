from textual import work, on
from textual.app import ComposeResult
from textual.containers import Container, Center
from textual.screen import Screen
from textual.widgets import Button, ContentSwitcher, Label, LoadingIndicator
from textual.reactive import var

from itmostalk.api import API
from itmostalk.db import functions as cache
from itmostalk.tui.widgets import TreeSelectionList, StepperHeader, StepperFooter

import asyncio


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
        from .main import MainScreen

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

        self.query_one("#status", Label).update(f"Получение расписания (0/{cnt})...")
        for index, potok_id in enumerate(potoks_to_fetch):
            self.query_one("#status", Label).update(
                f"Получение расписания ({index+1}/{cnt})..."
            )
            people = cache.get_potok_schedule(potok_id)
            if not people:
                people = await api.get_potok_schedule(potok_id)
        with cache.Session.begin() as session:
            info = session.query(cache.Info).filter(cache.Info.name=="setup_complete")
            if info:
                info.update({"value": "true"})
            else:
                session.add(cache.Info(name="setup_complete", value="true"))
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
