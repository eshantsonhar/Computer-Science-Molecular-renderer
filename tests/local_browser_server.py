"""Small local adapter for exercising the Vercel page and Python API together."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from api.geometry import handler as geometry_handler


class LocalBrowserHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _is_reaction_planner_request(self):
        return self.path.startswith("/api/geometry?") and "service=reaction_planner" in self.path

    def _send_json(self, status_code, body):
        return geometry_handler._send_json(self, status_code, body)

    def _send_error(self, status_code, code, message, kind, **extra):
        return geometry_handler._send_error(self, status_code, code, message, kind, **extra)

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/api/reaction_planner":
            self.path = "/api/geometry?service=reaction_planner"
            return geometry_handler.do_GET(self)
        if self.path.split("?", 1)[0] == "/api/geometry":
            return geometry_handler.do_GET(self)
        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path.split("?", 1)[0] == "/api/reaction_planner":
            self.path = "/api/geometry?service=reaction_planner"
        if self.path.split("?", 1)[0] in {"/api/reaction_planner", "/api/geometry"}:
            return geometry_handler.do_POST(self)
        return self.send_error(404)

    def log_message(self, format, *args):
        print(f"local-browser: {format % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 4173), LocalBrowserHandler)
    print("Local AtomView browser server listening at http://127.0.0.1:4173", flush=True)
    server.serve_forever()
