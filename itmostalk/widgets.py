from textual.app import App, ComposeResult
from textual.widgets import SelectionList, Button


class TreeSelectionList(SelectionList):
    groups: dict = None
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
            for element in elements:
                selections.append(tuple(element))
                self.groups[index].append(element[1])
        super().__init__(
            *selections, name=name, id=id, classes=classes, disabled=disabled
        )

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
