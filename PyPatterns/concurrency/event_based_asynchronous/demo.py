"""Event-based asynchronous — start async op; completion fires callback/event."""

from __future__ import annotations

import asyncio
from collections.abc import Callable


class AsyncDownloader:
    """Start a download asynchronously; invoke callback when complete."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None

    async def _fetch(self, url: str) -> str:
        await asyncio.sleep(0.05)
        return f"payload from {url}"

    def download_async(
        self,
        url: str,
        on_complete: Callable[[str, str | None, Exception | None], None],
    ) -> None:
        async def run() -> None:
            try:
                result = await self._fetch(url)
                on_complete(url, result, None)
            except Exception as exc:  # noqa: BLE001
                on_complete(url, None, exc)

        loop = asyncio.get_running_loop()
        loop.create_task(run())

    def download_sync(
        self,
        url: str,
        on_complete: Callable[[str, str | None, Exception | None], None],
    ) -> None:
        """Run from a non-async main() using a one-shot event loop."""
        asyncio.run(self._download_and_callback(url, on_complete))

    async def _download_and_callback(
        self,
        url: str,
        on_complete: Callable[[str, str | None, Exception | None], None],
    ) -> None:
        try:
            result = await self._fetch(url)
            on_complete(url, result, None)
        except Exception as exc:  # noqa: BLE001
            on_complete(url, None, exc)


def main() -> None:
    completed: list[str] = []

    def on_download_complete(
        url: str, result: str | None, error: Exception | None
    ) -> None:
        if error:
            print(f"FAILED {url}: {error}")
        else:
            completed.append(result or "")
            print(f"Completed: {result}")

    downloader = AsyncDownloader()
    urls = ["https://api.example/a", "https://api.example/b", "https://api.example/c"]

    async def run_all() -> None:
        for url in urls:
            downloader.download_async(url, on_download_complete)
        await asyncio.sleep(0.2)

    asyncio.run(run_all())
    print(f"Downloads finished: {len(completed)}/{len(urls)}")


if __name__ == "__main__":
    main()
