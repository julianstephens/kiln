"""Tests for RuntimeProcess startup and lifecycle."""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from kiln.sdk.errors import MissingRuntimeBinaryError, RuntimeProcessError
from kiln.sdk.runtime_process import RuntimeProcess, _find_runtime_binary


class TestFindRuntimeBinary:
    """Tests for _find_runtime_binary binary discovery."""

    def test_find_runtime_binary_from_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that KILN_RUNTIME_BINARY env var is used when set."""
        binary_path = "/opt/kiln/runtime"
        monkeypatch.setenv("KILN_RUNTIME_BINARY", binary_path)

        result = _find_runtime_binary()
        assert result == Path(binary_path)

    def test_find_runtime_binary_missing_raises_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that MissingRuntimeBinaryError is raised when binary is not found."""
        # Unset the env var so no binary is found
        monkeypatch.delenv("KILN_RUNTIME_BINARY", raising=False)

        with pytest.raises(
            MissingRuntimeBinaryError, match="runtime binary is missing"
        ):
            _find_runtime_binary()


class TestRuntimeProcessStartup:
    """Tests for RuntimeProcess.start() and initialization."""

    @pytest.mark.anyio
    async def test_start_returns_runtime_process_with_fake_process(
        self, mocker: Any
    ) -> None:
        """Test that start() creates and returns a RuntimeProcess instance."""
        # Create a fake process with stdin/stdout
        fake_process = SimpleNamespace(
            stdin=mocker.MagicMock(),
            stdout=mocker.MagicMock(),
            returncode=None,
        )

        # Mock the binary finding and process creation
        binary_path = Path("/opt/kiln/runtime")
        mocker.patch(
            "kiln.sdk.runtime_process._find_runtime_binary", return_value=binary_path
        )
        mocker.patch(
            "anyio.open_process",
            return_value=fake_process,
        )

        result = await RuntimeProcess.start()

        assert isinstance(result, RuntimeProcess)
        assert result.process == fake_process
        assert result.is_alive is True

    @pytest.mark.anyio
    async def test_start_with_explicit_binary_path(self, mocker: Any) -> None:
        """Test that start() accepts an explicit binary path."""
        fake_process = SimpleNamespace(
            stdin=mocker.MagicMock(),
            stdout=mocker.MagicMock(),
            returncode=None,
        )
        binary_path = Path("/custom/kiln-runtime")

        # Should not call _find_runtime_binary when binary is provided
        find_binary_mock = mocker.patch("kiln.sdk.runtime_process._find_runtime_binary")
        mocker.patch(
            "anyio.open_process",
            return_value=fake_process,
        )

        await RuntimeProcess.start(binary=binary_path)

        find_binary_mock.assert_not_called()

    @pytest.mark.anyio
    async def test_start_raises_missing_binary_error(self, mocker: Any) -> None:
        """Test that start() raises MissingRuntimeBinaryError when binary not found."""
        mocker.patch(
            "kiln.sdk.runtime_process._find_runtime_binary",
            side_effect=MissingRuntimeBinaryError(),
        )

        with pytest.raises(RuntimeProcessError, match="runtime binary is missing"):
            await RuntimeProcess.start()

    @pytest.mark.anyio
    async def test_start_posix_passes_correct_subprocess_args(
        self, mocker: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that POSIX startup passes correct arguments to anyio.open_process."""
        fake_process = SimpleNamespace(
            stdin=mocker.MagicMock(),
            stdout=mocker.MagicMock(),
            returncode=None,
        )
        binary_path = Path("/opt/kiln/runtime")

        # Mock platform detection to POSIX
        monkeypatch.setattr("sys.platform", "linux")

        open_process_mock = mocker.patch(
            "anyio.open_process",
            return_value=fake_process,
        )

        mocker.patch(
            "kiln.sdk.runtime_process._find_runtime_binary", return_value=binary_path
        )

        await RuntimeProcess.start()

        # Verify anyio.open_process was called with correct args
        open_process_mock.assert_called_once()
        call_args = open_process_mock.call_args
        assert call_args.kwargs["command"] == [str(binary_path)]
        # stdin and stdout should be set to subprocess.PIPE
        assert call_args.kwargs["stdin"] == subprocess.PIPE
        assert call_args.kwargs["stdout"] == subprocess.PIPE

    @pytest.mark.anyio
    async def test_start_windows_calls_create_windows_process(
        self, mocker: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that Windows startup calls create_windows_process."""
        fake_process = SimpleNamespace(
            stdin=mocker.MagicMock(),
            stdout=mocker.MagicMock(),
            returncode=None,
        )
        binary_path = Path("C:\\kiln\\runtime.exe")

        # Mock platform detection to Windows
        monkeypatch.setattr("sys.platform", "win32")

        create_windows_process_mock = mocker.patch(
            "kiln.sdk.runtime_process.create_windows_process",
            return_value=fake_process,
        )

        mocker.patch(
            "kiln.sdk.runtime_process._find_runtime_binary", return_value=binary_path
        )

        await RuntimeProcess.start()

        # Verify create_windows_process was called
        create_windows_process_mock.assert_called_once()
        call_args = create_windows_process_mock.call_args
        assert call_args.kwargs["command"] == str(binary_path)
        assert call_args.kwargs["args"] == []


class TestRuntimeProcessFailures:
    """Tests for RuntimeProcess failure modes."""

    @pytest.mark.anyio
    async def test_start_with_process_early_exit(self, mocker: Any) -> None:
        """Test detection of process that exits immediately after spawn."""
        # Process that has already exited with nonzero code
        fake_process = SimpleNamespace(
            stdin=mocker.MagicMock(),
            stdout=mocker.MagicMock(),
            returncode=1,  # Non-zero exit code
        )

        mocker.patch(
            "kiln.sdk.runtime_process._find_runtime_binary",
            return_value=Path("/opt/kiln/runtime"),
        )
        mocker.patch(
            "anyio.open_process",
            return_value=fake_process,
        )

        result = await RuntimeProcess.start()

        # Process is created, but is_alive property reflects exit
        assert result.is_alive is False
        assert result.process.returncode == 1

    @pytest.mark.anyio
    async def test_is_alive_property_reflects_process_state(self, mocker: Any) -> None:
        """Test that is_alive property correctly reflects process returncode."""
        fake_process = SimpleNamespace(
            stdin=mocker.MagicMock(),
            stdout=mocker.MagicMock(),
            returncode=None,
        )

        mocker.patch(
            "kiln.sdk.runtime_process._find_runtime_binary",
            return_value=Path("/opt/kiln/runtime"),
        )
        mocker.patch("anyio.open_process", return_value=fake_process)

        runtime_proc = await RuntimeProcess.start()

        # Process is alive
        assert runtime_proc.is_alive is True

        # Simulate process exit
        fake_process.returncode = 0
        assert runtime_proc.is_alive is False

    @pytest.mark.anyio
    async def test_aclose_terminates_posix_process(
        self, mocker: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that aclose() calls POSIX process termination."""
        fake_process = SimpleNamespace(
            stdin=mocker.MagicMock(),
            stdout=mocker.MagicMock(),
            returncode=None,
        )

        monkeypatch.setattr("sys.platform", "linux")

        mocker.patch(
            "kiln.sdk.runtime_process._find_runtime_binary",
            return_value=Path("/opt/kiln/runtime"),
        )
        mocker.patch("anyio.open_process", return_value=fake_process)
        terminate_mock = mocker.patch(
            "kiln.sdk.runtime_process.terminate_posix_process_tree"
        )

        runtime_proc = await RuntimeProcess.start()
        await runtime_proc.aclose()

        terminate_mock.assert_called_once_with(fake_process)

    @pytest.mark.anyio
    async def test_aclose_terminates_windows_process(
        self, mocker: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that aclose() calls Windows process termination."""
        fake_process = SimpleNamespace(
            stdin=mocker.MagicMock(),
            stdout=mocker.MagicMock(),
            returncode=None,
        )

        monkeypatch.setattr("sys.platform", "win32")

        mocker.patch(
            "kiln.sdk.runtime_process._find_runtime_binary",
            return_value=Path("C:\\kiln\\runtime.exe"),
        )
        mocker.patch(
            "kiln.sdk.runtime_process.create_windows_process",
            return_value=fake_process,
        )
        terminate_mock = mocker.patch(
            "kiln.sdk.runtime_process.terminate_windows_process_tree"
        )

        runtime_proc = await RuntimeProcess.start()
        await runtime_proc.aclose()

        terminate_mock.assert_called_once_with(fake_process)


class TestRuntimeProcessStderrHandling:
    """Tests for handling stderr output during startup."""

    @pytest.mark.anyio
    async def test_start_passes_stderr_to_sys_stderr(
        self, mocker: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that stderr is passed to sys.stderr (POSIX)."""
        fake_process = SimpleNamespace(
            stdin=mocker.MagicMock(),
            stdout=mocker.MagicMock(),
            returncode=None,
        )

        monkeypatch.setattr("sys.platform", "linux")

        open_process_mock = mocker.patch(
            "anyio.open_process",
            return_value=fake_process,
        )

        mocker.patch(
            "kiln.sdk.runtime_process._find_runtime_binary",
            return_value=Path("/opt/kiln/runtime"),
        )

        await RuntimeProcess.start()

        # Verify stderr is passed to sys.stderr
        call_args = open_process_mock.call_args
        assert call_args.kwargs["stderr"] == sys.stderr

    @pytest.mark.anyio
    async def test_start_passes_stderr_to_windows_process_creator(
        self, mocker: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that stderr is passed to create_windows_process (Windows)."""
        fake_process = SimpleNamespace(
            stdin=mocker.MagicMock(),
            stdout=mocker.MagicMock(),
            returncode=None,
        )

        monkeypatch.setattr("sys.platform", "win32")

        create_windows_process_mock = mocker.patch(
            "kiln.sdk.runtime_process.create_windows_process",
            return_value=fake_process,
        )

        mocker.patch(
            "kiln.sdk.runtime_process._find_runtime_binary",
            return_value=Path("C:\\kiln\\runtime.exe"),
        )

        await RuntimeProcess.start()

        # Verify errlog is passed
        call_args = create_windows_process_mock.call_args
        assert call_args.kwargs["errlog"] == sys.stderr

    @pytest.mark.anyio
    async def test_runtime_environment_includes_allowed_vars(
        self, mocker: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that only allowed environment variables are passed to process."""
        fake_process = SimpleNamespace(
            stdin=mocker.MagicMock(),
            stdout=mocker.MagicMock(),
            returncode=None,
        )

        monkeypatch.setattr("sys.platform", "linux")

        # Set various env vars
        monkeypatch.setenv("PATH", "/usr/bin")
        monkeypatch.setenv("HOME", "/home/user")
        monkeypatch.setenv("SECRET", "should-not-be-passed")

        open_process_mock = mocker.patch(
            "anyio.open_process",
            return_value=fake_process,
        )

        mocker.patch(
            "kiln.sdk.runtime_process._find_runtime_binary",
            return_value=Path("/opt/kiln/runtime"),
        )

        await RuntimeProcess.start()

        # Check env passed to process
        call_args = open_process_mock.call_args
        env = call_args.kwargs["env"]

        # Should include allowed vars
        assert "PATH" in env
        assert "HOME" in env
        # Should NOT include disallowed vars
        assert "SECRET" not in env
