from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from langchain_mongodb_deepagents_vfs.backends.base import (
    MAX_READ_BYTES,
    ObjectStoreBackend,
)
from langchain_mongodb_deepagents_vfs.errors import AdapterError, ErrorCode


class LocalBackend(ObjectStoreBackend):
    """ObjectStoreBackend backed by a directory on the local disk.

    Keys are POSIX paths relative to *root*: ``docs/a.md`` is ``<root>/docs/a.md``.
    The root is the isolation boundary (S3Backend's ``prefix`` plays this role).
    """

    # ---- Stage 0: skeleton -------------------------------------------------
    def __init__(self, root: str | os.PathLike[str]) -> None:
        # TODO: resolve and store the root.
        # TODO: raise AdapterError(E1001_MISSING_CONFIG) if it is not a directory.
        self.root= Path(root).expanduser().resolve()
        if not self.root.is_dir():
            raise AdapterError(ErrorCode.MISSING_CONFIG)
    
       

    # ---- Stage 1: path resolution (security) ------------------------------
    def _resolve(self, path: str) -> Path:
        """Map an untrusted key to a real path inside the root.

        Hint: compare S3Backend._key(). Which Path methods collapse ``..`` and
        follow symlinks? Do that BEFORE the containment check.
        Raise AdapterError(E2009_PATH_OUTSIDE_PREFIX) when it escapes.
        """

        target = (self.root / path).resolve()
        try:
            if not target.is_relative_to(self.root):
                raise AdapterError(ErrorCode.E2009_PATH_OUTSIDE_PREFIX)
        except ValueError:
            raise AdapterError(ErrorCode.E2009_PATH_OUTSIDE_PREFIX)
        return target

    # ---- Stage 2: read side -------------------------------------------------
    def get_size(self, path: str) -> int:
        """Size in bytes. E2001 if missing, E2002 for other OSErrors."""
        try: 
            return self.resolve(path).stat().st_size
        except FileNotFoundError:
            raise AdapterError(ErrorCode.E2001_FILE_NOT_FOUND)
        except OSError:
            raise AdapterError(ErrorCode.E2002_IO_ERROR)

    def read(self, path: str, offset: int = 0, limit: int = -1) -> bytes:
        """Bytes of *path*, sliced by byte offset / limit.

        Must never materialise more than MAX_READ_BYTES (raise E2002).
        Hint: how can you detect "too big" without reading the whole file?
        """
        try:
            file_path = self.resolve(path)
            with file_path.open("rb") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()

            if size>  MAX_READ_BYTES:
                raise AdapterError(ErrorCode.E2002_OBJECT_READ_FAILED)

            f.seek(offset)
            if limit == -1:
                return f.read(MAX_READ_BYTES+1)
            return f.read(min(limit,MAX_READ_BYTES)+1)
        except FileNotFoundError:
            raise AdapterError(ErrorCode.E2001_FILE_NOT_FOUND)
        except OSError:
            raise AdapterError(ErrorCode.E2002_IO_ERROR)

    # ---- Stage 3: write side --------------------------------------------------
    def write(self, path: str, content: bytes) -> None:
        """Create or replace *path*, creating parent directories.

        Refuse content larger than MAX_READ_BYTES (E2003): never store what
        read() would refuse. Wrap OSError as E2003.
        Think: the watcher polls at any moment. Can it see a half-written file?
        """
        try:
            file_path= self.resolve(path)
            file_path.parent.mkdir(parents= True,exist=True)
            file_path.write_bytes(content)
        except OSError:
            raise AdapterError(ErrorCode.E2003_OBJECT_WRITE_FAILED)

    # ---- Stage 4: change detection ---------------------------------------------
    def get_etag(self, key: str) -> str | None:
        """Current etag for *key*, or None if it does not exist.

        The watcher finds this with getattr(store, "get_etag", ...).
        """
        raise NotImplementedError

    def list_keys(self, prefix: str = "") -> Iterator[tuple[str, str]]:
        """Yield (key, etag) for every file whose key starts with *prefix*.

        Keys are POSIX-style and relative to the root, even on Windows.
        Wrap OSError as E2005. PollingWatcher diffs this output.
        """
        raise NotImplementedError

    # ---- Stage 5: edit -----------------------------------------------------------
    def edit(self, path: str, old: str, new: str, replace_all: bool = False) -> int:
        """Replace *old* with *new*; return the occurrences replaced.

        S3 uses If-Match for E2008 (conflict). The local disk has no such thing:
        what can you compare, and when, to detect a concurrent change?
        """
        raise NotImplementedError

    # ---- Stage 6: bulk helpers ----------------------------------------------------
    # upload_files / download_files are abstract in the ABC in the unmodified repo.
    # Implement them, compare with S3Backend, then refactor (see stage 6 notes).
    def upload_files(self, files):  # type: ignore[no-untyped-def]
        raise NotImplementedError

    def download_files(self, paths):  # type: ignore[no-untyped-def]
        raise NotImplementedError