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
        return environ

    def start_response(self, status, response_headers, exc_info=None):
        self.headers += response_headers
        self.response_code, self.response_message = status.split(" ")
        # IMPLEMENT

    def handle_request(self):
        print(">>> handle_request")
        env = self.get_environ()
        app = self.application
        result = app(env, self.start_response)
        self.finish_response(result)

    def finish_response(self, result):
        self.begin_response(self.response_code, self.response_message)
        for data in result:
            self.push(data)
        self.close()


def application(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'Hello World']

server = AsyncWSGIServer(handler_class=AsyncWSGIRequestHandler)
server.set_app(application)
server.serve_forever()
