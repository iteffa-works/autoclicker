"""Ensure a single GUI process; second launch asks the first to show the window."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

SERVER_NAME = "FlowaxyAutoclickerSingleInstance_v1"


class SingleInstanceGuard(QObject):
    """First process listens; second connects, sends a byte, exits."""

    activate_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_new_connection)

    def try_acquire(self) -> bool:
        """Return True if this process should continue; False if another is running."""
        probe = QLocalSocket()
        probe.connectToServer(SERVER_NAME)
        if probe.waitForConnected(400):
            try:
                probe.write(b"show\n")
                probe.flush()
                probe.waitForBytesWritten(500)
            finally:
                probe.disconnectFromServer()
            return False
        probe.close()
        QLocalServer.removeServer(SERVER_NAME)
        if not self._server.listen(SERVER_NAME):
            return True
        return True

    def _on_new_connection(self) -> None:
        conn = self._server.nextPendingConnection()
        if conn is None:
            return
        if conn.waitForReadyRead(800):
            conn.readAll()
        conn.disconnectFromServer()
        self.activate_requested.emit()
