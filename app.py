from __future__ import annotations

from core.ssl_config import configure_ssl_certificates

configure_ssl_certificates()

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
import os
import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
