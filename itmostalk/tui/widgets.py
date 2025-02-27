from textual.app import App, ComposeResult
from textual.widgets import SelectionList, Button, Label, ContentSwitcher, TabbedContent
from textual.containers import Horizontal, Container
from textual.message import Message
from textual.widget import Widget
from textual.widgets.selection_list import Selection


class StepperHeader(Horizontal):
    DEFAULT_CSS = """
        StepperHeader {
            background: $panel;
            dock: top;
            width: 100%;
            height: 1;
            align-horizontal: center;
        }
        .step-arrow {
            margin-left: 10;
            margin-right: 10;
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
            yield Step(self.steps[i])
            yield Label("->", classes="step-arrow")
        yield Step(self.steps[-1])


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
                    Selection("├" + element[0], element[1], disabled=True)
                )
                self.groups[index].append(element[1])
            element = elements[-1]
            selections.append(Selection("╰" + element[0], element[1]))
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
