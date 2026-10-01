#!/usr/bin/env python3
"""UI on :8080, API on :8000. /api is proxied. Ctrl-C stops both."""
import os
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
API = "http://127.0.0.1:8000"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "frontend"), **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            super().do_GET()

    def _proxy(self):
        try:
            upstream = urlopen(API + self.path)
        except URLError:
            self.send_error(502, "API is not up")
            return
        if self.path.startswith("/api/events"):
            self._stream(upstream)
            return
        body = upstream.read()
        ctype = upstream.headers.get("Content-Type", "application/json")
        status = upstream.status
        upstream.close()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _stream(self, upstream):
        # HTTP/1.1 needs chunked so the browser can read the open SSE body
        self.protocol_version = "HTTP/1.1"
        self.close_connection = True
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        try:
            while True:
                # read() waits for 1024 bytes; one SSE event is much smaller
                chunk = upstream.read1(1024)
                if not chunk:
                    self.wfile.write(b"0\r\n\r\n")
                    break
                self.wfile.write(f"{len(chunk):x}\r\n".encode())
                self.wfile.write(chunk)
                self.wfile.write(b"\r\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            upstream.close()


def main():
    env = {**os.environ, "DATA_DIR": str(ROOT / "data")}
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=ROOT / "backend",
        env=env,
    )
    print(
        "UI http://127.0.0.1:8080   API http://127.0.0.1:8000   metrics http://127.0.0.1:8000/metrics",
        flush=True,
    )
    try:
        ThreadingHTTPServer(("127.0.0.1", 8080), Handler).serve_forever()
    finally:
        api.terminate()
        api.wait()


if __name__ == "__main__":
    main()
