from __future__ import annotations

import os


def configure_ssl_certificates() -> None:
    """Configure certifi CA bundle for packaged builds."""
    try:
        import certifi
    except Exception:
        return

    ca_bundle = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", ca_bundle)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_bundle)
