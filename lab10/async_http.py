import asyncore
import asynchat
import socket
import multiprocessing
import logging
import mimetypes
import os
import urllib
import argparse
import time
import re

# _get_data()

def url_normalize(path):
    if path.startswith("."):
        path = "/" + path
    while "../" in path:
        p1 = path.find("/..")
        p2 = path.rfind("/", 0, p1)
        if p2 != -1:
            path = path[:p2] + path[p1+3:]
        else:
            path = path.replace("/..", "", 1)
    path = path.replace("/./", "/")
    path = path.replace("/.", "")
    return path


class FileProducer(object):

    def __init__(self, file, chunk_size=4096):
        self.file = file
        self.chunk_size = chunk_size

    def more(self):
        if self.file:
            data = self.file.read(self.chunk_size)
            if data:
                return data
            self.file.close()
            self.file = None
        return ""


class AsyncHTTPServer(asyncore.dispatcher):

    def __init__(self, host="127.0.0.1", port=9000):
        super().__init__()
        self.create_socket()
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def serve_forever(self):
        asyncore.loop()

    def handle_accepted(self, sock, addr):
        log.debug(f"Incoming connection from {addr}")
        AsyncHTTPRequestHandler(sock)

class AsyncHTTPRequestHandler(asynchat.async_chat):

    def __init__(self, sock):
        super().__init__(sock)
        self.term = "\r\n"
        self.server_host = '127.0.0.1'
        self.set_terminator(b"\r\n\r\n")
        self.headers = {} # incoming
        self.protocol_version = '1.1'
        self.response_lines = []

    def collect_incoming_data(self, data):
        log.debug(f"Incoming data: {data}")
        self._collect_incoming_data(data)
        self.headers_parsed = False

    def parse_request(self):
        if not self.headers_parsed:
            self.wrong_headers = False
            self.parse_headers()
            if self.wrong_headers:
                self.respond_with_error(400)
                return
            if self.method == 'POST':
                content_length = int(self.headers['content-length'])
                if content_length > 0:
                    self.set_terminator(content_length)
                    # дочитать
                    pass
                else:
                    self.handle_request()
            else:
                self.handle_request()
        else:
            self.parse_body()
            self.handle_request()


    def parse_headers(self):
        logging.debug('>>> parse_headers <<<')
        def list2dict(headers):
            result = {}
            for header in headers:
                key = header.split(':')[0].lower()
                value = header[len(key) + 2:] # Host + : + ' ' = len() + 2
                result[key] = value
            return result

        raw = self._get_data().decode()

        # parsing method
        self.method = re.findall('^[A-Z]+', raw)[0]
        logging.debug(f'Method: {self.method}')
        if not hasattr(self, 'do_' + self.method): # move to separate method
            self.wrong_headers = True
            return

        # parsing protocol version
        matches = re.findall('\/(1.1|1.0|0.9)\\r\\n', raw)
        if len(matches) == 0:
            self.wrong_headers = True
            return
        self.protocol_version = matches[0].strip().replace('/', '')
        logging.debug(f"protocol: {self.protocol_version}")

        # parsing request uri
        expression = f'^{self.method}(.*?)HTTP/{self.protocol_version}'
        matches = re.findall(expression, raw)
        if len(matches) == 0:
            self.wrong_headers = True
            return
        uri = matches[0]
        self.uri = uri[1:-1] # removing spaces from both sides
        self.uri = self.translate_path(self.uri)
        logging.debug(f"uri: '{self.uri}'")

        # parsing headers

        if self.method == 'GET':
            # 'GET / HTTP/1.1\r\nHost: 127.0.0.1:9000\r\nUser-Agent: curl/7.49.1\r\nAccept: */*'
            self.headers = list2dict(raw.split("\r\n")[1:])

            if self.protocol_version == '1.1' and 'host' not in self.headers:
                self.wrong_headers = True
                return

            self.headers_parsed = True

            # extracting query string
            if '?' in self.uri:
                temp = self.uri
                self.uri = re.findall('^(.*?)\?', temp)[0]
                self.query_string = temp[len(self.uri) + 1:] # 'http://mail.ru/get?a=b' <- len(uri) + 1 (?)
                logging.debug(f"uri: '{self.uri}', query_string: '{self.query_string}'")

        elif self.method == 'POST':
            # 'GET / HTTP/1.1\r\nHost: 127.0.0.1:9000\r\nUser-Agent: curl/7.49.1\r\nAccept: */*\r\n\r\nBodddyyyy\r\n\r\n'
            head = raw.split("\r\n" * 2)[:1][0]
            self.headers = list2dict(head.split("\r\n")[1:])

            if 'content-length' not in self.headers:
                self.wrong_headers = True
                return

            self.headers_parsed = True
        else:
            self.respond_with_error(405)

    def parse_body(self):
        logging.debug(">>> parse_body <<<")
        self.body = self._get_data().decode()

    def found_terminator(self):
        self.parse_request()

    def handle_request(self):
        method_name = 'do_' + self.method
        if not hasattr(self, method_name):
            self.respond_with_error(405)
            return
        handler = getattr(self, method_name)
        handler()

    responses = {
        200: ('OK', 'Request fulfilled, document follows'),
        400: ('Bad Request', 'Bad request syntax or unsupported method'),
        403: ('Forbidden', 'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed', 'Specified method is invalid for this resource.')
    }

    def respond_with_error(self, code, message=None):
        logging.debug('>> respond_with_error <<<')
        try:
            short_msg, long_msg = self.responses[code]
        except KeyError:
            short_msg, long_msg = "Shit happened", "Unexpected error"
        if message is None:
            message = short_msg

        self.respond_with_code(code, message)

    def fill_response_headers(self):
        server_headers = {
            'Date': self.date_time_string(),
            'Host': self.server_host
        }
        for key, value in server_headers.items():
            self.send_header(key, value)
        self.end_headers()

    def send_header(self, keyword, value):
        self.response_lines.append(f"{keyword}: {value}")

    def end_headers(self):
        self.response_lines.append('')

    def respond_with_code(self, code, message=None): # begin_headers
        logging.debug(">>> respond_with_code <<<")
        if message is None:
            try:
                message, _ = self.responses[code]
            except KeyError:
                message = 'Empty'
        self.response_lines = [f"HTTP/{self.protocol_version} {code} {message}"]
        self.fill_response_headers()

        if self.method == 'POST':
            self.response_lines.append(self.body)

        logging.debug(f"response_lines len: {len(self.response_lines)}")
        server_raw_response = self.term.join(self.response_lines)
        print(server_raw_response)
        self.handle_close()

    def date_time_string(self):
        weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        monthname = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(time.time())
        return f"{weekdayname[wd]}, {day} {monthname[month]} {year} {hh}:{mm}:{ss} GMT"

    def translate_path(self, path):
        if path.startswith("."):
            path = "/" + path
        while "../" in path:
            p1 = path.find("/..")
            p2 = path.rfind("/", 0, p1)
            if p2 != -1:
                path = path[:p2] + path[p1+3:]
            else:
                path = path.replace("/..", "", 1)
        path = path.replace("/./", "/")
        path = path.replace("/.", "")
        return path

    def do_GET(self):
        # find document by uri
        self.respond_with_code(200)

    def do_HEAD(self):
        pass

    def do_POST(self):
        self.respond_with_code(200)

def parse_args():
    parser = argparse.ArgumentParser("Simple asynchronous web-server")
    parser.add_argument("--host", dest="host", default="127.0.0.1")
    parser.add_argument("--port", dest="port", type=int, default=9001)
    parser.add_argument("--log", dest="loglevel", default="debug")
    parser.add_argument("--logfile", dest="logfile", default=None)
    parser.add_argument("-w", dest="nworkers", type=int, default=1)
    parser.add_argument("-r", dest="document_root", default=".")
    return parser.parse_args()

def run():
    server = AsyncHTTPServer(host=args.host, port=args.port)
    server.serve_forever()

if __name__ == "__main__":
    args = parse_args()

    logging.basicConfig(
        filename=args.logfile,
        level=getattr(logging, args.loglevel.upper()),
        format="%(name)s: %(process)d %(message)s")
    log = logging.getLogger(__name__)

    DOCUMENT_ROOT = args.document_root
    # for _ in range(args.nworkers):
    p = multiprocessing.Process(target=run)
    p.start()
