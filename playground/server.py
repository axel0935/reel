"""A lightweight local server for the Reel web playground.

Uses only the Python standard library (http.server).
Communicates with the Reel language interpreter via core/reel/api.py.
"""

import http.server
import json
from pathlib import Path
import sys
import urllib.parse

# Locate project directories
PLAYGROUND_DIR = Path(__file__).resolve().parent
ROOT_DIR = PLAYGROUND_DIR.parent
CORE_DIR = ROOT_DIR / "core"
EXAMPLES_DIR = ROOT_DIR / "examples"

# Add core/ to sys.path according to project contract
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

try:
    from reel.api import run
except ImportError as err:
    # Fallback placeholder if run cannot be imported
    def run(source: str) -> dict:
        return {"output": "", "error": f"Failed to load Reel engine: {err}"}


class ReelPlaygroundHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler serving playground static assets and the Reel run API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PLAYGROUND_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/examples":
            self._handle_get_examples()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/run":
            self._handle_post_run()
        else:
            self.send_error(404, "Endpoint not found")

    def _handle_get_examples(self):
        """Returns all .reel files from the examples directory."""
        examples = []
        if EXAMPLES_DIR.exists():
            for file_path in sorted(EXAMPLES_DIR.glob("*.reel")):
                try:
                    code = file_path.read_text(encoding="utf-8")
                    examples.append({
                        "filename": file_path.name,
                        "code": code
                    })
                except Exception as read_err:
                    print(f"Warning: could not read {file_path.name}: {read_err}")

        payload = json.dumps({"examples": examples}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(payload)

    def _handle_post_run(self):
        """Executes Reel code via core/reel/api.py run()."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode("utf-8"))
            source = body.get("source", "")
        except Exception as parse_err:
            result = {"output": "", "error": f"Invalid request body: {parse_err}"}
        else:
            result = run(source)

        payload = json.dumps(result).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        """Clean minimal server logging to stdout."""
        sys.stdout.write(f"[Reel Playground] {self.address_string()} - {format % args}\n")
        sys.stdout.flush()


def run_server(port: int = 8000):
    server_address = ("127.0.0.1", port)
    http.server.HTTPServer.allow_reuse_address = True
    with http.server.HTTPServer(server_address, ReelPlaygroundHandler) as httpd:
        print(f"\n========================================================")
        print(f"🎬 Reel Studio Playground is running!")
        print(f"👉 Open in your browser: http://localhost:{port}")
        print(f"========================================================\n")
        print("Press Ctrl+C to stop the server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down playground server. Bye!")


if __name__ == "__main__":
    port_num = 8000
    if len(sys.argv) > 1:
        try:
            port_num = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port '{sys.argv[1]}', using 8000.")
    run_server(port_num)
