import async_http
import os
import sys

class AsyncWSGIServer(async_http.AsyncHTTPServer):

    def set_app(self, application):
        self.application = application

    def get_app(self):
        return self.application

class AsyncWSGIRequestHandler(async_http.AsyncHTTPRequestHandler):

    def get_environ(self):
        environ = dict(os.environ.items())
        environ['wsgi.input'] = sys.stdin
        environ['wsgi.errors'] = sys.stderr
        environ['wsgi.version'] = (1, 0)
        environ['wsgi.multithread'] = False
        environ['wsgi.multiprocess'] = False
        environ['wsgi.run_once'] = True

        if hasattr(self, 'query_string'):
            environ['QUERY_STRING'] = self.query_string
        return environ

    def start_response(self, status, response_headers, exc_info=None):
        if exc_info:
            raise AssertionError("exc_info is not None")
        for key, value in response_headers:
            self.server_headers[key] = value
        self.response_code, self.response_message = status.split(" ")[:2]

    def handle_request(self):
        env = self.get_environ()
        app = server.get_app()
        result = app(env, self.start_response)
        self.finish_response(result)

    def finish_response(self, result):
        self.begin_response(self.response_code, self.response_message)
        for data in result:
            self.push(data)
        self.end_response()
        self.close()


def application(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'Hello World']

server = AsyncWSGIServer(handler_class=AsyncWSGIRequestHandler)
server.set_app(application)
server.serve_forever()
