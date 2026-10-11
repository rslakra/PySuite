

"""In-memory buffers for files that are open in a language server."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

from solidlsp.ls_process import LanguageServerProcess
from solidlsp.lsp_protocol_handler.lsp_constants import LSPConstants

from .base import FileUtils


class LanguageServerHandle(Protocol):
    """The part of a language server that :class:`LSPFileBuffer` relies on.

    Declared structurally instead of importing ``SolidLanguageServer`` so that ``symbols`` can import this
    module without a circular import (``SolidLanguageServer`` satisfies this protocol).
    """

    server: LanguageServerProcess


class LSPFileBuffer:
    """
    This class is used to store the contents of an open LSP file in memory.
    """

    def __init__(
        self,
        abs_path: Path,
        uri: str,
        encoding: str,
        version: int,
        language_id: str,
        ref_count: int,
        language_server: LanguageServerHandle,
        open_in_ls: bool = True,
    ) -> None:
        self.abs_path = abs_path
        self.language_server = language_server
        self.uri = uri
        self._read_file_modified_date: float | None = None
        self._contents: str | None = None
        self.version = version
        self.language_id = language_id
        self.ref_count = ref_count
        self.encoding = encoding
        self._content_hash: str | None = None
        self._is_open_in_ls = False
        if open_in_ls:
            self._open_in_ls()

    def _open_in_ls(self) -> None:
        """
        Open the file in the language server if it is not already open.
        """
        if self._is_open_in_ls:
            return
        self._is_open_in_ls = True
        self.language_server.server.notify.did_open_text_document(
            {
                LSPConstants.TEXT_DOCUMENT: {  # type: ignore
                    LSPConstants.URI: self.uri,
                    LSPConstants.LANGUAGE_ID: self.language_id,
                    LSPConstants.VERSION: 0,
                    LSPConstants.TEXT: self.contents,
                }
            }
        )

    def close(self) -> None:
        if self._is_open_in_ls:
            self.language_server.server.notify.did_close_text_document(
                {
                    LSPConstants.TEXT_DOCUMENT: {  # type: ignore
                        LSPConstants.URI: self.uri,
                    }
                }
            )

    def ensure_open_in_ls(self) -> None:
        """Ensure that the file is opened in the language server."""
        self._open_in_ls()

    @property
    def contents(self) -> str:
        file_modified_date = self.abs_path.stat().st_mtime

        # if contents are cached, check if they are stale (file modification since last read) and invalidate if so
        if self._contents is not None:
            assert self._read_file_modified_date is not None
            if file_modified_date > self._read_file_modified_date:
                self._contents = None

        if self._contents is None:
            self._read_file_modified_date = file_modified_date
            self._contents = FileUtils.read_file(str(self.abs_path), self.encoding)
            self._content_hash = None

        return self._contents

    @contents.setter
    def contents(self, new_contents: str) -> None:
        """
        Sets new contents for the file buffer (in-memory change only).
        Persistence of the change to disk must be handled separately.

        :param new_contents: the new contents to set
        """
        self._contents = new_contents
        self._content_hash = None

    @property
    def content_hash(self) -> str:
        if self._content_hash is None:
            self._content_hash = hashlib.md5(
                self.contents.encode(self.encoding)
            ).hexdigest()
        return self._content_hash

    def split_lines(self) -> list[str]:
        """Splits the contents of the file into lines."""
        return self.contents.split("\n")


