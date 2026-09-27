#!/usr/bin/env python3
"""
Native Desktop Entry Point for macOS (and Windows).
Uses macOS WebKit (WKWebView) via pywebview to display the application
in a native OS window (no browser tabs, no address bar, no terminal required).
"""
import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import webview
from backend.app import app


def main():
    # Pass the Flask WSGI app directly to pywebview.
    # It runs an internal in-process engine with zero external port exposure.
    window = webview.create_window(
        title="Anki Japanese Grammar Studio",
        url=app,
        width=1240,
        height=860,
        min_size=(900, 600),
        text_select=True,
    )
    # Start the native Cocoa/WebKit desktop window
    webview.start(debug=False)


if __name__ == "__main__":
    main()
