"""Microkernel architecture — minimal core with pluggable feature modules."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Plugin(ABC):
    """Contract every plugin module must implement."""

    name: str

    @abstractmethod
    def execute(self, data: str) -> str:
        ...


class MicroKernel:
    """Core runtime — registers plugins and dispatches work."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        self._plugins[plugin.name] = plugin
        print(f"[Kernel] registered plugin: {plugin.name}")

    def run(self, plugin_name: str, data: str) -> str:
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise KeyError(f"unknown plugin: {plugin_name}")
        return plugin.execute(data)


class UppercasePlugin(Plugin):
    name = "uppercase"

    def execute(self, data: str) -> str:
        return data.upper()


class ReversePlugin(Plugin):
    name = "reverse"

    def execute(self, data: str) -> str:
        return data[::-1]


class WordCountPlugin(Plugin):
    name = "wordcount"

    def execute(self, data: str) -> str:
        return str(len(data.split()))


def main() -> None:
    kernel = MicroKernel()
    kernel.register(UppercasePlugin())
    kernel.register(ReversePlugin())
    kernel.register(WordCountPlugin())

    text = "hello microkernel world"
    for name in ("uppercase", "reverse", "wordcount"):
        result = kernel.run(name, text)
        print(f"[{name}] → {result}")
    print("Core stays stable — add features by loading new plugins")


if __name__ == "__main__":
    main()
