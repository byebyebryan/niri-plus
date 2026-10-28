#!/usr/bin/env python3
"""Serve the local browser/files and display-capture fixture on loopback."""

from __future__ import annotations

from email.parser import BytesParser
from email.policy import default
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import re
import sys
from urllib.parse import urlparse


PAGE = Path(__file__).resolve().parent / "sample-site/index.html"
SAMPLE_NAME = "niri-plus-desktop-sample.md"
SAMPLE_BYTES = (
    b"# Niri Plus local desktop sample\n\n"
    b"This file was downloaded from the local reference guest fixture.\n"
    b"Open it from Dolphin, then upload the same file through Chrome's file picker.\n"
    b"\n"
    b"The upload endpoint checks the original bytes and stores nothing on disk.\n"
)
SAMPLE_SHA256 = sha256(SAMPLE_BYTES).hexdigest()
IMAGE_NAME = "niri-plus-desktop-sample.svg"
IMAGE_BYTES = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">'
    b'<rect width="640" height="360" fill="#1b1d1f"/>'
    b'<rect x="24" y="24" width="592" height="312" rx="8" fill="#25282a" stroke="#81878c"/>'
    b'<rect x="48" y="48" width="544" height="56" rx="4" fill="#111315"/>'
    b'<rect x="48" y="48" width="8" height="56" fill="#6eafff"/>'
    b'<rect x="48" y="132" width="330" height="20" rx="4" fill="#efefec"/>'
    b'<rect x="48" y="170" width="450" height="12" rx="4" fill="#aaaeac"/>'
    b'<rect x="48" y="194" width="384" height="12" rx="4" fill="#aaaeac"/>'
    b'<rect x="48" y="236" width="196" height="56" rx="4" fill="#294e75" stroke="#a6ceff"/>'
    b'<circle cx="517" cy="264" r="28" fill="#6eafff"/>'
    b'</svg>\n'
)
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
BOUNDARY_PATTERN = re.compile(rb"^[0-9A-Za-z'()+_,./:=?-]{1,200}$")


class FixtureServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False


class Handler(BaseHTTPRequestHandler):
    server_version = "NiriPlusLocalFixture/1"

    def log_message(self, format_string, *args):
        sys.stdout.write("fixture: " + format_string % args + "\n")

    def _send(self, status: int, body: bytes, content_type: str, *, extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; media-src 'self' blob:; img-src 'self' data:; object-src 'none'; base-uri 'none'; form-action 'self'")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/" or path == "/index.html":
            self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            return
        if path == "/healthz":
            self._send(200, b"ok\n", "text/plain; charset=utf-8")
            return
        if path == f"/sample/{SAMPLE_NAME}":
            self._send(
                200,
                SAMPLE_BYTES,
                "text/markdown; charset=utf-8",
                extra_headers={"Content-Disposition": f'attachment; filename="{SAMPLE_NAME}"'},
            )
            return
        if path == f"/sample/{IMAGE_NAME}":
            self._send(
                200,
                IMAGE_BYTES,
                "image/svg+xml",
                extra_headers={"Content-Disposition": f'attachment; filename="{IMAGE_NAME}"'},
            )
            return
        if path == f"/assets/{IMAGE_NAME}":
            self._send(200, IMAGE_BYTES, "image/svg+xml")
            return
        self._send(404, b"Not found\n", "text/plain; charset=utf-8")

    def do_POST(self):
        if urlparse(self.path).path != "/upload":
            self._send_json(404, {"message": "Unknown upload route."})
            return
        content_length_text = self.headers.get("Content-Length", "")
        try:
            content_length = int(content_length_text)
        except ValueError:
            self._send_json(411, {"message": "A valid Content-Length is required."})
            return
        if content_length <= 0 or content_length > MAX_UPLOAD_BYTES:
            self._send_json(413, {"message": "Upload must be between 1 byte and 2 MiB."})
            return

        content_type = self.headers.get("Content-Type", "")
        try:
            media_header = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("ascii", "strict")
            parsed_header = BytesParser(policy=default).parsebytes(media_header)
        except (UnicodeError, ValueError):
            self._send_json(400, {"message": "Malformed multipart content type."})
            return
        boundary = parsed_header.get_param("boundary")
        if not isinstance(boundary, str) or not BOUNDARY_PATTERN.fullmatch(boundary.encode("ascii", "ignore")):
            self._send_json(400, {"message": "Malformed multipart boundary."})
            return
        if parsed_header.get_content_type() != "multipart/form-data":
            self._send_json(415, {"message": "Use the browser file form (multipart/form-data)."})
            return

        body = self.rfile.read(content_length)
        if len(body) != content_length:
            self._send_json(400, {"message": "The upload body was incomplete."})
            return
        message = BytesParser(policy=default).parsebytes(media_header + body)
        if not message.is_multipart():
            self._send_json(400, {"message": "The upload form was not multipart."})
            return
        uploads = []
        for part in message.iter_parts():
            disposition = part.get_content_disposition()
            if disposition != "form-data" or part.get_param("name", header="content-disposition") != "file":
                continue
            filename = part.get_filename()
            payload = part.get_payload(decode=True)
            if filename is not None and payload is not None:
                uploads.append((filename, payload))
        if len(uploads) != 1:
            self._send_json(400, {"message": "Choose exactly one file in the browser picker."})
            return

        filename, payload = uploads[0]
        if filename != SAMPLE_NAME:
            self._send_json(422, {"message": f"Choose the downloaded {SAMPLE_NAME} sample."})
            return
        received_hash = sha256(payload).hexdigest()
        if received_hash != SAMPLE_SHA256 or payload != SAMPLE_BYTES:
            self._send_json(422, {"message": "The selected file does not match the downloaded sample."})
            return
        self._send_json(200, {
            "message": f"Received {filename}; the uploaded bytes match the downloaded sample.",
            "sha256": received_hash,
            "bytes": len(payload),
        })

    def _send_json(self, status: int, payload: dict[str, object]):
        body = (json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")


def main() -> int:
    if not PAGE.is_file() or PAGE.is_symlink():
        raise SystemExit(f"Sample fixture page is missing or unsafe: {PAGE}")
    server = FixtureServer(("127.0.0.1", 8765), Handler)
    print("Local desktop fixture: http://127.0.0.1:8765/ (Ctrl+C to stop)", flush=True)
    print(f"Download: /sample/{SAMPLE_NAME}; upload SHA-256: {SAMPLE_SHA256}", flush=True)
    print(f"Image sample: /sample/{IMAGE_NAME}; {len(IMAGE_BYTES)} SVG bytes", flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("Stopping the local fixture.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
