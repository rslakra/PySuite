"""Adapter pattern — European plug to US socket."""


class EuropeanPlug:
    """Two-round-pin plug supplying 230 V."""

    voltage = 230

    def connect(self) -> str:
        return f"European plug connected at {self.voltage}V"


class USPlug:
    """Flat-blade plug expected by a US socket."""

    voltage = 120

    def connect(self) -> str:
        return f"US plug connected at {self.voltage}V"


class EuropeanToUSAdapter(USPlug):
    """Adapts a EuropeanPlug so it fits a US socket interface."""

    def __init__(self, european: EuropeanPlug) -> None:
        self._european = european

    def connect(self) -> str:
        stepped = self._european.voltage // 2
        return (
            f"Adapter: {self._european.connect()} → "
            f"converted to {stepped}V for US socket"
        )


class USSocket:
    """Accepts only USPlug-compatible connectors."""

    def plug_in(self, plug: USPlug) -> str:
        if not isinstance(plug, USPlug):
            raise TypeError(f"{type(plug).__name__} is not compatible with US sockets")
        return f"Socket powered: {plug.connect()}"


def main() -> None:
    socket = USSocket()
    us_plug = USPlug()
    eu_plug = EuropeanPlug()
    adapter = EuropeanToUSAdapter(eu_plug)

    print(socket.plug_in(us_plug))
    print(socket.plug_in(adapter))
    try:
        socket.plug_in(eu_plug)  # type: ignore[arg-type]
    except TypeError:
        print("Direct EU plug rejected — adapter required")


if __name__ == "__main__":
    main()
