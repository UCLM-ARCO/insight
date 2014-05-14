# -*- mode: python; coding: utf-8 -*-

import time
from multiprocessing import Process, Event
from queue import Full
from threading import Thread
from PIL import Image
from io import BytesIO

from .tools import logger, IPCIface


class JPGConverterWorker(Thread):
    def __init__(self, name, size, src, dst):
        super().__init__()
        self.name = name
        self.size = size
        self.src = src
        self.dst = dst

        self.daemon = True
        self.should_stop = Event()

    def stop(self):
        logger.debug(" STOP ConverterWorker for {}".format(self.name))
        self.should_stop.set()

    def run(self):
        logger.debug(" START ConverterWorker for {}".format(self.name))
        while not self.should_stop.is_set():
            data = self.src.get()
            img = Image.frombuffer("RGBA", self.size, data, "raw", "RGBA", 0, 1)
            data = BytesIO()
            img.save(data, "JPEG")

            try:
                self.dst.put_nowait(data)
            except Full:
                pass


class JPGConverter(Process, IPCIface):
    def __init__(self, in_queue_pool, out_queue_pool):
        Process.__init__(self)
        IPCIface.__init__(self)

        self.daemon = True
        self.in_queue_pool = in_queue_pool
        self.out_queue_pool = out_queue_pool
        self.workers = {}
        self.should_stop = Event()

    def stop(self):
        self.should_stop.set()

    def run(self):
        while not self.should_stop.is_set():
            self.ipc_process()
            time.sleep(0.1)

    def _add_camera(self, name, size, src_index, dst_index):
        camera = dict(
            name = name,
            size = size,
            src = self.in_queue_pool.get(src_index),
            dst = self.out_queue_pool.get(dst_index),
        )

        thread = JPGConverterWorker(**camera)
        thread.start()
        camera['thread'] = thread
        self.workers[camera['name']] = camera

    # this method is "remote"
    def add_camera(self, camera):
        camera = dict(
            name = camera['name'],
            size = camera['size'],
            src_index = camera['src_index'],
            dst_index = camera['dst_index'],
        )

        self.ipc_invoke("_add_camera", **camera)
