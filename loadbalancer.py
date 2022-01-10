import json

from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
import requests
# from httplib import HTTPResponse
from os import curdir,sep

class RequestHandler(BaseHTTPRequestHandler):

    protocol_version = 'HTTP/1.0'

    def do_GET(self):
        # Parse request
        b=open('backend.json')
        backend= json.load(b)

        url = 'http://{}{}'.format(backend["backends"][0], self.path)
        req_header = self.parse_headers()
        
        # Call the target service
        resp = requests.get(url, headers=req_header, verify=False)

        # Respond with the requested data
        self.send_response(resp.status_code)
        self.send_resp_headers(resp)
        self.wfile.write(resp.content)
        return

    def parse_headers(self):
        req_header = {}
        for line in self.headers:
            line_parts = [o.strip() for o in line.split(':', 1)]
            if len(line_parts) == 2:
                req_header[line_parts[0]] = line_parts[1]
        return req_header

    def send_resp_headers(self, resp):
        respheaders = resp.headers
        print ('Response Header')
        for key in respheaders:
            if key not in ['Content-Encoding', 'Transfer-Encoding', 'content-encoding', 'transfer-encoding', 'content-length', 'Content-Length']:
                print (key, respheaders[key])
                self.send_header(key, respheaders[key])
        self.send_header('Content-Length', len(resp.content))
        self.end_headers()

def run():
    print('http server is starting...')
    #by default http server port is 80
    server_address = ('127.0.0.1', 8080)
    httpd = ThreadingHTTPServer(server_address, RequestHandler)
    try:
        print('http server is running...')
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.socket.close()

if __name__ == '__main__':
    run()
