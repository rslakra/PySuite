"""Facade pattern — HomeTheaterFacade simplifies subsystem startup."""

import time


class Amplifier:
    def on(self) -> str:
        return "Amplifier on"

    def set_volume(self, level: int) -> str:
        return f"Volume set to {level}"


class DvdPlayer:
    def on(self) -> str:
        return "DVD player on"

    def play(self, movie: str) -> str:
        return f"Playing '{movie}'"


class Projector:
    def on(self) -> str:
        return "Projector on"

    def wide_screen(self) -> str:
        return "Wide-screen mode enabled"


class HomeTheaterFacade:
    """Single entry point for the home theater subsystem."""

    def __init__(self) -> None:
        self.amp = Amplifier()
        self.dvd = DvdPlayer()
        self.projector = Projector()

    def watch_movie(self, movie: str) -> list[str]:
        steps = [
            self.amp.on(),
            self.amp.set_volume(5),
            self.projector.on(),
            self.projector.wide_screen(),
            self.dvd.on(),
            self.dvd.play(movie),
        ]
        time.sleep(0.05)  # simulate subsystem coordination delay
        return steps


def main() -> None:
    theater = HomeTheaterFacade()
    for step in theater.watch_movie("Design Patterns: The Movie"):
        print(step)
    print("\nEnjoy the show — one call did it all.")


if __name__ == "__main__":
    main()
