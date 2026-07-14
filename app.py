from __future__ import annotations

import os
import sys

import certifi

from core.ssl_config import configure_ssl_certificates

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
configure_ssl_certificates()


def main():
    from PySide6.QtWidgets import QApplication

    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
