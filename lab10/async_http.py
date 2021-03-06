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
from urllib import parse

class AsyncHTTPServer(asyncore.dispatcher):

    def __init__(self, host="127.0.0.1", port=9001, handler_class=None):
        super().__init__()
        self.handler_class = handler_class
        self.create_socket()
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def serve_forever(self):
        asyncore.loop()

    def handle_accepted(self, sock, addr):
        logging.debug(f"Incoming connection from {addr}")
        self.handler_class(sock)

def conv(s):
    return bytes(str(s), 'utf-8')

class AsyncHTTPRequestHandler(asynchat.async_chat):

    def __init__(self, sock):
        super().__init__(sock)
        self.term = "\r\n"
        self.server_host = '127.0.0.1'
        self.set_terminator(b"\r\n\r\n")
        self.headers = {} # incoming
        self.protocol_version = '1.1'
        self.headers_parsed = False
        self.server_headers = { # outgoing
            'Host': self.server_host,
            'Server': 'piechart',
            'Date': self.date_time_string()
        }

    def collect_incoming_data(self, data):
        logging.debug(f"Incoming data: {data}")
        self._collect_incoming_data(data)

    def parse_request(self):
        logging.debug(f"parse_request: self.headers_parsed == {self.headers_parsed}")
        if not self.headers_parsed:
            if not self.parse_headers():
                self.respond_with_code(400)
                return
            if self.method == 'POST':
                content_length = int(self.headers['content-length'])
                if content_length > 0:
                    logging.debug(f"Need to fetch {content_length} more bytes")
                    self.set_terminator(content_length)
                else:
                    self.body = ''
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
        if not hasattr(self, 'do_' + self.method):
            self.respond_with_code(405)
            return False

        # parsing protocol version
        matches = re.findall('\/(1.1|1.0|0.9)\\r\\n', raw)
        if len(matches) == 0:
            return False
        self.protocol_version = matches[0].strip().replace('/', '')
        logging.debug(f"protocol: {self.protocol_version}")

        # parsing request uri
        expression = f'^{self.method}(.*?)HTTP/{self.protocol_version}'
        matches = re.findall(expression, raw)
        if len(matches) == 0:
            return False
        uri = matches[0]
        self.uri = uri[1:-1] # removing spaces from both sides
        self.uri = parse.unquote(self.uri) # URLDecode
        self.uri = self.translate_path(self.uri)
        logging.debug(f"uri: '{self.uri}'")

        # parsing headers

        if self.method in ('GET', 'HEAD'):
            # 'GET / HTTP/1.1\r\nHost: 127.0.0.1:9000\r\nUser-Agent: curl/7.49.1\r\nAccept: */*'
            self.headers = list2dict(raw.split(self.term)[1:])

            if self.protocol_version == '1.1' and 'host' not in self.headers:
                return False

            # extracting query string
            if '?' in self.uri:
                temp = self.uri
                self.uri = re.findall('^(.*?)\?', temp)[0]
                self.query_string = temp[len(self.uri) + 1:] # 'http://mail.ru/get?a=b' <- len(uri) + 1 (?)
                logging.debug(f"uri: '{self.uri}', query_string: '{self.query_string}'")

        elif self.method == 'POST':
            # 'GET / HTTP/1.1\r\nHost: 127.0.0.1:9000\r\nUser-Agent: curl/7.49.1\r\nAccept: */*\r\n\r\nBodddyyyy\r\n\r\n'
            head = raw.split(self.term * 2)[:1][0]
            self.headers = list2dict(head.split(self.term)[1:])

            if 'content-length' not in self.headers:
                return False

        return True

    def parse_body(self):
        logging.debug(">>> parse_body <<<")
        self.body = self._get_data().decode()

    def found_terminator(self):
        self.parse_request()

    def handle_request(self):
        method_name = 'do_' + self.method
        if hasattr(self, method_name):
            handler = getattr(self, method_name)
            handler()

    responses = {
        200: ('OK', 'Request fulfilled, document follows'),
        400: ('Bad Request', 'Bad request syntax or unsupported method'),
        403: ('Forbidden', 'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed', 'Specified method is invalid for this resource.'),
        415: ('Client Error', 'Unsupported Media Type')
    }

    # send first response line and headers
    def begin_response(self, code, message):
        self.push(conv(f"HTTP/{self.protocol_version} {code} {message}"))
        self.add_terminator()
        for key, value in self.server_headers.items():
            self.send_header(key.title(), value)
        self.add_terminator()

    def send_header(self, keyword, value):
        self.push(conv(f"{keyword}: {value}"))
        self.add_terminator()

    def add_terminator(self):
        self.push(conv(self.term))

    def respond_with_code(self, code, content=''): # begin_headers
        logging.debug(f">>> respond_with_code: {code} <<<")
        try:
            message, _ = self.responses[code]
        except KeyError:
            message = 'Hell'

        self.begin_response(code, message)
        self.send_response(content)
        self.end_response()
        self.handle_close()

    def send_response(self, content):
        if self.method == 'POST':
            self.push(conv(self.body))
        else:
            if len(content) > 0: # requested uri
                self.push(conv(content))
                
    def end_response(self):
        self.add_terminator()
        self.add_terminator()

    def date_time_string(self):
        weekdayname = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
        monthname = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(time.time())
        return f"{weekdayname[wd]}, {day} {monthname[month]} {year} {hh}:{mm}:{ss} GMT"

    def translate_path(self, path):
        if path.startswith("."):
            path = "/" + path
        while "../" in path:
            p1 = path.find("/..")
            p2 = path.find("/", 0, p1)
            if p2 != -1:
                path = path[:p2] + path[p1 + 3:]
            else:
                path = path.replace("/..", "", 1)
        path = path.replace("/./", "/")
        path = path.replace("/.", "")

        if path == '/':
            path += 'index.html'
        if path.startswith('/'): # removing slash from beginning
            path = path[1:]
        return path

    text_extensions = ('html', 'txt', 'css', 'js')
    images_extensions = ('jpg', 'jpeg', 'png', 'gif')

    def do_GET(self, without_content=False):
        # find document by uri
        logging.debug(f"do_GET: uri == '{self.uri}'")

        valid_extensions = self.text_extensions + self.images_extensions
        max_extension_length = len(max(valid_extensions, key=len)) + 1 # 1 is for dot

        is_file = '.' in self.uri[-max_extension_length:]

        if not is_file: # wtf??
            self.respond_with_code(403)
            return

        if os.path.exists(self.uri):
            extension = self.uri.split(".")[-1:][0]
            if extension in valid_extensions:
                self.server_headers['content-type'] = self.make_content_type_header(extension)

                reading_mode = 'r' if extension in self.text_extensions else 'rb'
                with open(self.uri, reading_mode) as f:
                    data = f.read()
                    self.server_headers['content-length'] = len(data)
                if without_content: # called from do_HEAD
                    data = ''

                self.respond_with_code(200, data)
            else:
                self.respond_with_code(415)
        else:
            self.respond_with_code(404)

    def convert_extension_to_content_type_ending(self, s):
        replacements = [('txt', 'plain'), ('js', 'javascript'), ('jpg', 'jpeg')]
        for item in replacements:
            s = s.replace(item[0], item[1])
        return s

    def make_content_type_header(self, extension):
        first_part = 'text' if extension in self.text_extensions else 'image'
        extension = self.convert_extension_to_content_type_ending(extension)
        return f"{first_part}/{extension}"

    def do_HEAD(self):
        self.do_GET(without_content=True)

    def do_POST(self):
        if self.uri.endswith('.html'): # naive
            logging.debug("do_POST: Sending error 400 because of self.uri.endswith('.html')")
            self.respond_with_code(400)
        else:
            self.server_headers['content-length'] = len(self.body)
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
    server = AsyncHTTPServer(host=args.host, port=args.port, handler_class=AsyncHTTPRequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    args = parse_args()

    logging.basicConfig(
        filename=args.logfile,
        level=getattr(logging, args.loglevel.upper()),
        format="%(name)s: %(process)d %(message)s")
    log = logging.getLogger(__name__)

    DOCUMENT_ROOT = args.document_root
    for _ in range(args.nworkers):
        p = multiprocessing.Process(target=run)
        p.start()
