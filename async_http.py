import asyncore
import asynchat
import socket
import multiprocessing
import logging
import mimetypes
import os
from urlparse import parse_qs
import urllib
import argparse
import time


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


class AsyncServer(asyncore.dispatcher):

    def __init__(self, host="127.0.0.1", port=9000):
        pass

    def handle_accept(self):
        pass

    def serve_forever(self):
        pass


class AsyncHTTPRequestHandler(asynchat.async_chat):

    def __init__(self, sock):
        super().__init__(sock)
        self.terminator = "\r\n"
        self.set_terminator(b(str(self.terminator * 2)))

    def collect_incoming_data(self, data):
        log.debug(f"Incoming data: {data}")
        self._collect_incoming_data(data)

    def found_terminator(self):
        self.headers_parsed = False
        self.parse_request()

    def parse_request(self):
        if not self.headers_parsed:
            self.parse_headers()
            if self.headers_parsing_failed:
                self.send_error(400)
                self.handle_close()
            if self.method == 'POST':
                length = self.headers.getheader('content-length')
                if length.isnumeric():
                    if int(length) > 0:
                        # дочитать запрос
                        return
                self.handle_request()
        else:
            # получить тело
            self.handle_request()


    def parse_headers(self):
        ###
        # on fail: self.headers_parsing_failed = True
        ###

    def handle_request(self):
        method_name = 'do_' + self.method
        if not hasattr(self, method_name):
            self.send_error(405)
            self.handle_close()
            return
        handler = getattr(self, method_name)
        handler()

    def send_header(self, keyword, value):
        self.wfile.write(f"{keyword}: {value}{self.terminator}")

    def send_error(self, code, message=None):
        try:
            short_msg, long_msg = self.responses[code]
        except KeyError:
            short_msg, long_msg = "Unexpected error", "Unexpected error"
        if message is None:
            message = short_msg

        self.send_response(code, message)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Connection", "close")
        self.end_headers()

    def send_response(self, code, message=None):
        pass

    def end_headers(self):
        self.wfile.write(self.terminator)

    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    monthname = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def date_time_string(self):
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(time.time())
        return f"{self.weekdayname[wd]}, {day} {self.monthname[month]} {year} {hh}:{mm}:{ss} GMT"
        
    def send_head(self):
        pass

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
        pass

    def do_HEAD(self):
        pass

    responses = {
        200: ('OK', 'Request fulfilled, document follows'),
        400: ('Bad Request',
            'Bad request syntax or unsupported method'),
        403: ('Forbidden',
            'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed',
            'Specified method is invalid for this resource.'),
    }


def parse_args():
    parser = argparse.ArgumentParser("Simple asynchronous web-server")
    parser.add_argument("--host", dest="host", default="127.0.0.1")
    parser.add_argument("--port", dest="port", type=int, default=9000)
    parser.add_argument("--log", dest="loglevel", default="info")
    parser.add_argument("--logfile", dest="logfile", default=None)
    parser.add_argument("-w", dest="nworkers", type=int, default=1)
    parser.add_argument("-r", dest="document_root", default=".")
    return parser.parse_args()

def run():
    server = AsyncServer(host=args.host, port=args.port)
    server.serve_forever()

if __name__ == "__main__":
    args = parse_args()

    logging.basicConfig(
        filename=args.logfile,
        level=getattr(logging, args.loglevel.upper()),
        format="%(name)s: %(process)d %(message)s")
    log = logging.getLogger(__name__)

    DOCUMENT_ROOT = args.document_root
    for _ in xrange(args.nworkers):
        p = multiprocessing.Process(target=run)
        p.start()
