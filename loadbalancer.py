import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.client import parse_headers
from threading import Lock

import requests


class ThreadSafeIncrementer:
    def __init__(self, num_backends):
        self.value = 0
        self.num_backends = num_backends
        self._lock = Lock()

    def nextindex(self):
        with self._lock:
            self.value = (self.value + 1) % self.num_backends
            return self.value


global_current_backend = 0


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):

        is_request_healthy = False
        num_backends_tried = 0

        while not is_request_healthy and num_backends_tried < NUM_BACKENDS:

            # We pick a backend here
            idx = global_current_backend.nextindex()

            url = f"http://{backends[idx]}/{self.path}"
            req_header = self.parse_headers()

            try:
                resp = requests.get(url, headers=req_header, verify=False, timeout=3)
            except requests.ConnectTimeout or requests.exceptions.ReadTimeout as e:
                self.send_response(504)
                self.wfile.write("Upstream timed out".encode("utf-8"))
                return

            print("UPSTREAM STATUS:", resp.status_code)
            is_request_healthy = True
            if resp.status_code // 100 == 5:
                is_request_healthy = False
                num_backends_tried += 1

        if num_backends_tried >= NUM_BACKENDS:
            self.send_response(500)
            self.send_resp_headers(resp)
            self.wfile.write("No backend available".encode("utf-8"))
        else:
            self.send_response(resp.status_code)
            self.send_resp_headers(resp)
            self.wfile.write(resp.content)

        return

    def parse_headers(self):
        req_header = {}
        for line in self.headers:
            line_parts = [o.strip() for o in line.split(":", 1)]
            if len(line_parts) == 2:
                req_header[line_parts[0]] = line_parts[1]
        return req_header

    def send_resp_headers(self, resp):
        respheaders = resp.headers
        for header_name in respheaders:
            if header_name not in [
                "Content-Encoding",
                "Transfer-Encoding",
                "content-encoding",
                "transfer-encoding",
                "content-length",
                "Content-Length",
                "Connection",
            ]:
                self.send_header(header_name, respheaders[header_name])
        self.send_header("Content-Length", len(resp.content))
        self.end_headers()


def run():
    LISTEN_ADDR = "0.0.0.0"
    LISTEN_PORT = 3000
    print("Starting HTTP Listener")
    server_address = (LISTEN_ADDR, LISTEN_PORT)
    httpd = ThreadingHTTPServer(server_address, RequestHandler)
    try:
        print(f"Listening for connections at http://{LISTEN_ADDR}:{LISTEN_PORT}/")
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.socket.close()


NUM_BACKENDS = 0


if __name__ == "__main__":
    with open("backend.json") as f:
        backends = json.load(f)["backends"]
    NUM_BACKENDS = len(backends)
    global_current_backend = ThreadSafeIncrementer(NUM_BACKENDS)
    run()
