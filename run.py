#!/usr/bin/env python3
"""
Launcher for Anki Japanese Grammar Studio.
Starts the local server and prints access URLs (localhost and LAN for Android devices).
"""
import os
import socket
import sys
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.app import app


def get_lan_ip() -> str:
    """Finds the local network IP so mobile devices (Android) can connect on Wi-Fi."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    port = 5001
    lan_ip = get_lan_ip()

    print("=" * 65)
    print(" 🌸  ANKI JAPANESE GRAMMAR STUDIO - LOCAL SERVER STARTED  🌸")
    print("=" * 65)
    print(f" ▶ macOS / Desktop:   http://localhost:{port}")
    print(f" ▶ Android / LAN:       http://{lan_ip}:{port}")
    print("=" * 65)
    print(" Press Ctrl+C to stop the server.")
    print("=" * 65)

    # Automatically open in default browser on launch
    webbrowser.open(f"http://localhost:{port}")

    app.run(host="0.0.0.0", port=port, debug=False)
