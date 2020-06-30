import os

import tornado.ioloop
import tornado.web


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(5000, ssl_options={
        "certfile": os.path.join("certificates", "server.crt"),
        "keyfile": os.path.join("certificates", "server.key"),
    })
    tornado.ioloop.IOLoop.current().start()