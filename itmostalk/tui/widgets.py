from textual.app import ComposeResult
from textual.widgets import (
    SelectionList,
    Button,
    Label,
)
from textual.containers import Horizontal
from textual.widgets.selection_list import Selection
from textual.events import Click


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
        step = (
            self.query_one("#step" + str(index))
            .add_class("completed")
            .remove_class("current")
        )

    def set_current(self, index: int):
        self.log("ALO BLYAT")
        self.query_one("#step" + str(index)).add_class("current").remove_class(
            "completed"
        )
        for i in range(len(self.steps)):
            if i != index:
                self.query_one("#step" + str(i)).remove_class("current")


class StepperFooter(Horizontal):
    DEFAULT_CSS = """
        StepperFooter {
            dock: bottom;
            width: 100%;
            height: 3;
        }
        .button-next {
            dock: right;
        }
        .button-prev {
            dock: left;
        }
    """

    def compose(self) -> ComposeResult:
        yield Button("< Prev", classes="button-prev")
        yield Button("Next >", classes="button-next")


class TreeSelectionList(SelectionList):
    groups: dict[int, list[tuple[int, str]]] = None
    programmatic_update = False

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
            for i in range(len(elements) - 1):
                element = elements[i]
                selections.append((" ├── " + element[0], element[1]))
                self.groups[index].append(element[1])
            element = elements[-1]
            selections.append((" ╰── " + element[0], element[1]))
            self.groups[index].append(elements[-1][1])
        self.add_options(selections)

    def on_selection_list_selection_toggled(
        self, event: SelectionList.SelectionToggled
    ) -> None:
        if self.programmatic_update:
            return
        self.programmatic_update = True
        try:
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
        finally:
            self.programmatic_update = False
