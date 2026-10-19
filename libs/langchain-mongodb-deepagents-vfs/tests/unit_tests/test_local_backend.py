
"""Unit tests for LocalBackend.

STARTING POINT for the interview.
Copy to: libs/langchain-mongodb-deepagents-vfs/tests/unit_tests/test_local_backend.py

Each stage lists the tests to write FIRST (red), then the implementation (green).
Remove the skip marker as you reach each test. Model after test_s3_backend.py,
but use pytest's tmp_path instead of moto.
"""

from __future__ import annotations

import pytest
import langchain_mongodb_deepagents_vfs.backends.locals as locals
from langchain_mongodb_deepagents_vfs.errors import AdapterError, ErrorCode


@pytest.fixture
def backend(tmp_path):
    return locals.LocalBackend(tmp_path)


# ---- Stage 0 ---------------------------------------------------------------
@pytest.mark.unit
class TestLocalBackendInit:
    def test_missing_directory_raises(self, tmp_path):
        # Arrange: a path under tmp_path that does not exist
        # Act/Assert: LocalBackend() raises AdapterError with code E1001
        
        pass

# ---- Stage 1: path resolution ---------------------------------------------------
@pytest.mark.skip(reason="stage 1")
@pytest.mark.unit
class TestLocalBackendRootScope:
    # Drive through a public method (e.g. write or read), like
    # TestPrefixScopeEnforcement in test_s3_backend.py.
    def test_dotdot_traversal_is_refused(self, backend):
        # "../outside.txt" and "a/../../outside.txt" -> E2009
        for path in("../outside.txt", "a/../../outside.txt"):
            with pytest.raises(AdapterError) as exec_info:
                backend.read(path, offset=0)
            assert exec_info.value.code == ErrorCode.E2009_PATH_OUTSIDE_PREFIX
    def test_symlink_escape_is_refused(self, backend, tmp_path):
        # Create a file OUTSIDE tmp_path, symlink to it from inside, read it -> E2009

        outside_path= tmp_path/"outside.txt"
        outside_path.write_text("something")
        symlink_path= tmp_path/"link.txt"
        try: 
            symlink_path.symlink_to(outside_path)
        except( OSError, NotImplementedError):
            pytest.skip("symlinks not supported on this platform")  
        with pytest.raises(AdapterError) as exec_info:
            backend.read(outside_path, offset=0)
        assert exec_info.value.code == ErrorCode.E2009_PATH_OUTSIDE_PREFIX                                                                          

    def test_leading_slash_is_relative_to_root(self, backend, tmp_path):
        # write("/a.txt") must land at <root>/a.txt, not at the filesystem root
        
        pass


# ---- Stage 2: read side ------------------------------------------------------------
@pytest.mark.skip(reason="stage 2")
@pytest.mark.unit
class TestLocalBackendRead:
    def test_get_size(self, backend, tmp_path):
        file_path= tmp_path/ "test.txt"
        file_path.write_bytes(b"Hello, world!")
        assert backend.get_size("test.txt") == 13
    def test_get_size_missing_raises(self, backend):  # E2001
        with pytest.raises(AdapterError) as exc_info:
            backend.get_size("missing.txt")
        assert exc_info.value.code == ErrorCode.E2001_FILE_NOT_FOUND

    def test_read_with_offset_and_limit(self, backend, tmp_path):
        # "0123456789", offset=2, limit=3 -> b"234"
        
        file_path= tmp_path/"test.txt"
        file_path.write_bytes(b"Hello")
        assert backend.read("test.txt",offset=2,limit=3) == b"llo"

    def test_read_missing_raises(self, backend):  # E2001
        
        with pytest.raises(AdapterError) as exc_info:
            backend.read("missing.txt",offset=0)
        assert exc_info.value.code == ErrorCode.E2001_FILE_NOT_FOUND

    def test_read_enforces_cap(self, backend, tmp_path, monkeypatch):
        # Patch MAX_READ_BYTES in the local module to a tiny value (see
        # TestReadSizeCap in test_s3_backend.py), write cap+1 bytes -> E2002

        pass
        


# ---- Stage 3: write side --------------------------------------------------------------
@pytest.mark.skip(reason="stage 3")
@pytest.mark.unit
class TestLocalBackendWrite:
    def test_write_then_read_creates_parent_dirs(self, backend, tmp_path):
        
        backend.write("subdir/test.txt", b"Hello, world!")
        assert (tmp_path/"subdir/test.txt").read_bytes() == b"Hello, world!"
        assert backend.read("subdir/test.txt") == b"Hello, world!"
    
    def test_write_overwrites(self, backend):
        
        backend.write("test.txt", b"First")
        backend.write("test.txt", b"Second")
        assert backend.read("test.txt", offset=0) == b"Second"
    def test_write_refuses_oversized_content(self, backend, monkeypatch):  # E2003
        
        monkeypatch.setattr("langchain_mongodb_deepagents_vfs.backends.locals.MAX_READ_BYTES", 5)
        with pytest.raises(AdapterError) as exec_info:
            backend.write("test.txt", b"Content that exceeds the limit")

        assert exec_info.value.code == ErrorCode.E2003_OBJECT_WRITE_FAILED

    def test_no_temp_files_left_behind(self, backend, tmp_path):
        # After a write, only the target file exists in its directory

        pass
        
        


# ---- Stage 4: change detection ----------------------------------------------------------
@pytest.mark.skip(reason="stage 4")
@pytest.mark.unit
class TestLocalBackendListKeys:

    def test_lists_nested_files_as_posix_keys(self, backend):
        pass

    def test_prefix_filters(self, backend):
        pass

    def test_etag_changes_when_content_changes(self, backend):
        pass

    def test_get_etag_missing_is_none(self, backend):
        pass


# ---- Stage 5: edit -----------------------------------------------------------------------
@pytest.mark.skip(reason="stage 5")
@pytest.mark.unit
class TestLocalBackendEdit:
    def test_edit_replaces_first_occurrence(self, backend):
        pass

    def test_edit_replace_all(self, backend):
        pass

    def test_edit_missing_raises(self, backend):  # E2001
        pass

    def test_edit_conflict_raises(self, backend, monkeypatch):
        # Simulate a concurrent change between read and write (hint: the etag
        # seen before the edit differs from the one seen just before the swap) -> E2008
        pass


# ---- Stage 6: bulk helpers ------------------------------------------------------------------
@pytest.mark.skip(reason="stage 6")
@pytest.mark.unit
class TestLocalBackendBulk:
    def test_upload_reports_per_path_errors(self, backend):
        # One good path, one "../bad.txt": expect one response each, in order,
        # with error set only on the bad one
        pass

    def test_download_reports_per_path_errors(self, backend):
        pass