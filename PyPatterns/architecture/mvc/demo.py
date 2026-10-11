"""Model–View–Controller — separate data, presentation, and input handling."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TaskModel:
    """Model owns state and business rules."""

    items: list[str] = field(default_factory=list)

    def add(self, title: str) -> None:
        title = title.strip()
        if not title:
            raise ValueError("title required")
        self.items.append(title)

    def count(self) -> int:
        return len(self.items)


class TaskView:
    """View renders model state — no business logic."""

    def render(self, model: TaskModel) -> str:
        lines = [f"Tasks ({model.count()}):"]
        for index, title in enumerate(model.items, start=1):
            lines.append(f"  {index}. {title}")
        return "\n".join(lines)


class TaskController:
    """Controller handles user actions and updates model + view."""

    def __init__(self, model: TaskModel, view: TaskView) -> None:
        self._model = model
        self._view = view

    def create_task(self, title: str) -> str:
        self._model.add(title)
        return self._view.render(self._model)


def main() -> None:
    model = TaskModel()
    view = TaskView()
    controller = TaskController(model, view)

    for title in ("Write demo", "Review README", "Run tests"):
        print(controller.create_task(title))
        print()

    print("Model holds data; View displays; Controller coordinates user input")


if __name__ == "__main__":
    main()
