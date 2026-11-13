"""A lightweight local server for the Reel web playground.

Uses only the Python standard library (http.server).
Runs Reel code safely in a separate subprocess with a 5-second timeout,
refuses scripts over 20 KB, and binds strictly to 127.0.0.1.
"""

import http.server
import json
from pathlib import Path
import subprocess
import sys
import urllib.parse

# Locate project directories
PLAYGROUND_DIR = Path(__file__).resolve().parent
ROOT_DIR = PLAYGROUND_DIR.parent
CORE_DIR = ROOT_DIR / "core"
EXAMPLES_DIR = ROOT_DIR / "examples"
RUNNER_SCRIPT = PLAYGROUND_DIR / "runner.py"

# Safety limits
HOST = "127.0.0.1"
DEFAULT_PORT = 8000
MAX_CODE_SIZE_BYTES = 20 * 1024  # 20 KB (20,480 bytes)
TIMEOUT_SECONDS = 5.0  # 5 seconds execution limit


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

    def _send_json(self, data: dict, status_code: int = 200):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(payload)

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

        self._send_json({"examples": examples})

    def _handle_post_run(self):
        """Safely executes Reel code in a separate process with limits."""
        content_length = int(self.headers.get("Content-Length", 0))

        # Safety Check 1: Refuse payloads larger than 20 KB
        if content_length > MAX_CODE_SIZE_BYTES:
            self._send_json({
                "output": "",
                "error": f"The script is too large ({content_length:,} bytes). Maximum allowed size is 20 KB."
            })
            return

        try:
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode("utf-8"))
            source = body.get("source", "")
        except Exception as parse_err:
            self._send_json({
                "output": "",
                "error": f"Invalid request body: {parse_err}"
            })
            return

        # Safety Check 2: Verify UTF-8 byte length of code
        source_bytes_len = len(source.encode("utf-8"))
        if source_bytes_len > MAX_CODE_SIZE_BYTES:
            self._send_json({
                "output": "",
                "error": f"The script is too large ({source_bytes_len:,} bytes). Maximum allowed size is 20 KB."
            })
            return

        # Safety Check 3: Run code in a separate process with a 5-second timeout
        try:
            proc = subprocess.run(
                [sys.executable, str(RUNNER_SCRIPT)],
                input=source.encode("utf-8"),
                capture_output=True,
                timeout=TIMEOUT_SECONDS,
            )

            if proc.returncode != 0:
                stderr_text = proc.stderr.decode("utf-8", errors="replace").strip()
                result = {
                    "output": "",
                    "error": f"Execution interrupted: {stderr_text or 'Subprocess crashed'}"
                }
            else:
                stdout_text = proc.stdout.decode("utf-8", errors="replace")
                result = json.loads(stdout_text)
        except subprocess.TimeoutExpired:
            result = {
                "output": "",
                "error": "Scene timed out: execution took longer than 5 seconds. Did a loop run forever?"
            }
        except Exception as exec_err:
            result = {
                "output": "",
                "error": f"Could not execute scene: {exec_err}"
            }

        self._send_json(result)

    def log_message(self, format, *args):
        """Clean minimal server logging to stdout."""
        sys.stdout.write(f"[Reel Playground] {self.address_string()} - {format % args}\n")
        sys.stdout.flush()


def run_server(port: int = DEFAULT_PORT):
    # Safety Check: strictly bind to 127.0.0.1 only
    server_address = (HOST, port)
    http.server.HTTPServer.allow_reuse_address = True
    with http.server.HTTPServer(server_address, ReelPlaygroundHandler) as httpd:
        print("\n========================================================")
        print("🎬 Reel Studio Playground is running!")
        print(f"👉 Local address: http://{HOST}:{port}")
        print("   Listening on 127.0.0.1 only.")
        print("   Safety limits: 20 KB max code, 5 second timeout.")
        print("========================================================\n")
        print("Press Ctrl+C to stop the server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down playground server. Bye!")


if __name__ == "__main__":
    port_num = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port_num = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port '{sys.argv[1]}', using {DEFAULT_PORT}.")
    run_server(port_num)
