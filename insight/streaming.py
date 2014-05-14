# -*- mode: python; coding: utf-8 -*-

import os
from multiprocessing import Process, Event
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

from .tools import IPCIface


class StreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        cameraid = self.get_camera_id()
        if cameraid is None:
            return

        try:
            self.write_stream(cameraid)
        except BrokenPipeError:
            pass

    def get_camera_id(self):
        name = os.path.split(self.path)[-1]

        if not name in self.server.camera_pool.keys():
            self.send_error(404, "Camera '{0}' not found!".format(name))
            return None

        return name

    def write_stream(self, name):
        self.send_response(200)
        self.send_header('Content-type',
                         'multipart/x-mixed-replace; boundary=--jpgboundary')
        self.end_headers()

        data = self.server.camera_pool[name]
        while not self.server.should_stop.is_set():

            frame = data.get()
            frame = frame.getvalue()

            self.wfile.write(bytes("--jpgboundary", "utf-8"))
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', str(len(frame)))
            self.end_headers()

            self.wfile.write(frame)


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass


class StreamServer(Process, IPCIface):
    def __init__(self, out_queue_pool):
        Process.__init__(self)
        IPCIface.__init__(self)

        self.daemon = True
        self.out_queue_pool = out_queue_pool
        self.should_stop = Event()
        self.camera_pool = {}

    # this method is "remote"
    def add_camera(self, camera):
        camera = dict(
            name = camera['name'],
            size = camera['size'],
            dst_index = camera['dst_index'],
        )

        self.ipc_invoke("_add_camera", **camera)

    def _add_camera(self, name, size, dst_index):
        self.camera_pool[name] = self.out_queue_pool.get(dst_index)

    def stop(self):
        self.should_stop.set()

    def run(self):
        self.server = ThreadingHTTPServer(('', 8080), StreamHandler)
        self.server.camera_pool = self.camera_pool
        self.server.should_stop = self.should_stop
        self.serve_forever()

    def serve_forever(self):
        self.server.timeout = 0.1
        while not self.should_stop.is_set():
            try:
                self.server.handle_request()
            except KeyboardInterrupt:
                self.server.socket.close()
                break

            self.ipc_process()
