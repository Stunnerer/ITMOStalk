from datetime import time
from textual.app import ComposeResult
from textual.widgets import (
    SelectionList,
    Button,
    Label,
)
from textual.containers import Horizontal, Container
from textual.widgets.selection_list import Selection
from textual.events import Click
from textual.reactive import reactive

from typing import Any


class Step(Label):
    DEFAULT_CSS = """
        Step {
            text-align: center;
            padding: 0;
            margin: 0;
            padding-left: 4;
            padding-right: 4;
            
            &:hover {
                background: $boost;
            }
        }
    """
    num: int = 0

    def __init__(self, renderable="", num=0, *, classes=None):
        self.num = num
        super().__init__(renderable, id=f"step{num}", classes=classes)

    def on_click(self, event: Click):
        self.screen.current_step = self.num


class StepperHeader(Horizontal):
    DEFAULT_CSS = """
        StepperHeader {
            background: $panel;
            dock: top;
            width: 100%;
            height: 1;
            align-horizontal: center;
            & > .step-arrow {
                margin: 0;
                padding: 0;
                width: 2;
            }
        }
    """
    steps: list[str] = None

    def __init__(
        self,
        steps: list[str],
        name=None,
        id=None,
        classes=None,
        disabled=False,
        markup=True,
    ):
        self.steps = list(steps)
        super().__init__(
            name=name, id=id, classes=classes, disabled=disabled, markup=markup
        )

    def compose(self) -> ComposeResult:
        for i in range(len(self.steps) - 1):
            yield Step(self.steps[i], i)
            # yield Label("->", classes="step-arrow")
        i += 1
        yield Step(self.steps[i], i)

    def set_completed(self, index: int):
        (
            self.query_one("#step" + str(index))
            .add_class("success")
            .remove_class("primary")
        )

    def set_error(self, index: int):
        (
            self.query_one("#step" + str(index))
            .remove_class("success")
            .add_class("error")
        )

    def set_current(self, index: int):
        if index < 0:
            return
        self.query_one("#step" + str(index)).add_class("primary").remove_class(
            "success"
        ).disabled = True
        for i in range(len(self.steps)):
            if i != index:
                self.query_one("#step" + str(i)).remove_class(
                    "primary"
                ).disabled = False


class StepperFooter(Horizontal):
    DEFAULT_CSS = """
        StepperFooter {
            dock: bottom;
            width: 100%;
            height: 5;
            & > Button {
                margin: 1 2;
                height: 3;
                width: 1fr;
            }
            & > Label {
                width: 1fr;
                margin: 2;
                text-align: center;
            }
        }
    """

    def compose(self) -> ComposeResult:
        yield Button("< Prev", id="prev", disabled=True)
        yield Label("Status", id="status", disabled=True)
        yield Button("Next >", id="next", disabled=True)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "next":
            self.screen.current_step += 1
        else:
            self.screen.current_step -= 1


class TreeSelectionList(SelectionList):
    groups: dict[int, list[tuple[int, str]]] = None

    def __init__(
        self,
        groups: dict[str, list[tuple[str, int]]] = {},
        name=None,
        id=None,
        classes=None,
        disabled=False,
    ):
        selections = []
        self.groups = {}
        index = 0
        for group, elements in groups.items():
            index -= 1
            self.groups[index] = []
            selections.append((group, index))
            for i in range(len(elements) - 1):
                element = elements[i]
                selections.append(
                    Selection("├── " + element[0], element[1], disabled=True)
                )
                self.groups[index].append(element[1])
            element = elements[-1]
            selections.append(Selection("╰── " + element[0], element[1]))
            self.groups[index].append(elements[-1][1])
        super().__init__(
            *selections, name=name, id=id, classes=classes, disabled=disabled
        )

    def set_options(self, groups: dict[str, list[tuple[str, int]]]):
        self.clear_options()
        selections = []
        self.groups = {}
        index = 0
        for group, elements in groups.items():
            index -= 1
            self.groups[index] = []
            selections.append((group, index))
            padding = 2
            if "[" in group and "]" in group:
                padding = (group.index("]") - group.index("[")) // 2
            for i in range(len(elements) - 1):
                element = elements[i]
                selections.append((" " * padding + "├── " + element[0], element[1]))
                self.groups[index].append(element[1])
            element = elements[-1]
            selections.append((" " * padding + "╰── " + element[0], element[1]))
            self.groups[index].append(elements[-1][1])
        self.add_options(selections)

    def on_selection_list_selection_toggled(
        self, event: SelectionList.SelectionToggled
    ) -> None:
        selection_list = event.selection_list
        current_selection = set(selection_list.selected)
        selection = event.selection

        if selection.value in self.groups.keys():
            elements = self.groups[selection.value]
            if selection.value in current_selection:
                [selection_list.select(e) for e in elements]
            else:
                [selection_list.deselect(e) for e in elements]
        else:
            for group_idx, elements in self.groups.items():
                if selection.value in elements:
                    if group_idx in current_selection:
                        selection_list.deselect(group_idx)
                    elif all(e in current_selection for e in elements):
                        selection_list.select(group_idx)


class ScheduleEntry(Horizontal):

    DEFAULT_CSS = """
        ScheduleEntry {
            height: 4;
            margin: 1;
            & > .time {
                width: 7;
                & > Label {
                    width: 100%;
                    text-align: center;
                }
            }
            & >.info {
                width: 100%;
            }
        }
    """

    def __init__(
        self,
        start: time,
        end: time,
        subject: str,
        location: str,
        teacher: str,
        potok: str = "qwe",
        name=None,
        id=None,
        classes=None,
    ):
        self.start = start
        self.end = end
        self.subject = subject
        self.location = location
        self.teacher = teacher
        self.potok = potok
        super().__init__(name=name, id=id, classes=classes)

    def compose(self):
        with Container(classes="time"):
            yield Label(self.start.strftime("%H:%M"))
            yield Label("↓")
            yield Label(self.end.strftime("%H:%M"))
        with Container(classes="info"):
            yield Label(self.subject, variant="primary")
            yield Label(self.potok)
            yield Label(self.teacher)
            yield Label(self.location, variant="secondary")


class Schedule(Container):
    DEFAULT_CSS = """
        Schedule {
            width: 50;
            margin: 0 2;
            & > Label {
                width: 100%;
                margin: 1 0;
                text-align: center;
            }
            & > #schedule {
                padding: 0 1;
                width: 100%;
                background: $panel;
            }
        }
    """

    day = reactive("01.01.2000", recompose=True)
    entries = reactive([], recompose=True)

    def __init__(
        self,
        day: str = "01.01.2000",
        entries: list[dict[str, Any]] = [],
        name=None,
        id=None,
        classes=None,
    ):
        super().__init__(name=name, id=id, classes=classes)
        self.day = day
        self.entries = entries

    def compose(self):
        yield Label(self.day)
        with Container(id="schedule"):
            for entry in self.entries:
                yield ScheduleEntry(**entry)
