"""Abstract Factory — create families of related UI widgets without naming concrete classes."""

from abc import ABC, abstractmethod


class Button(ABC):
    @abstractmethod
    def paint(self) -> str: ...


class Checkbox(ABC):
    @abstractmethod
    def paint(self) -> str: ...


class WinButton(Button):
    def paint(self) -> str:
        return "[Win] Button"


class WinCheckbox(Checkbox):
    def paint(self) -> str:
        return "[Win] Checkbox"


class MacButton(Button):
    def paint(self) -> str:
        return "[Mac] Button"


class MacCheckbox(Checkbox):
    def paint(self) -> str:
        return "[Mac] Checkbox"


class UIFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button: ...

    @abstractmethod
    def create_checkbox(self) -> Checkbox: ...


class WinFactory(UIFactory):
    def create_button(self) -> Button:
        return WinButton()

    def create_checkbox(self) -> Checkbox:
        return WinCheckbox()


class MacFactory(UIFactory):
    def create_button(self) -> Button:
        return MacButton()

    def create_checkbox(self) -> Checkbox:
        return MacCheckbox()


def render_form(factory: UIFactory) -> None:
    button = factory.create_button()
    checkbox = factory.create_checkbox()
    print(f"  {button.paint()}")
    print(f"  {checkbox.paint()}")


def main() -> None:
    print("Windows look:")
    render_form(WinFactory())
    print("macOS look:")
    render_form(MacFactory())


if __name__ == "__main__":
    main()
