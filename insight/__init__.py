# -*- mode: python; coding: utf-8 -*-

import bpy

from .tools import inject_owner, logger, on_game_stop, ImageRenderSetup, QueuePool
from .converter import JPGConverter
from .streaming import StreamServer


@inject_owner
def init(owner):
    for a in bpy.context.screen.areas:
        if a.type == "VIEW_3D" and a.spaces[0].viewport_shade != "TEXTURED":
            logger.error("INVALID viewport/shade mode, set it to TEXTURED")
            return

    in_queue_pool = QueuePool()
    out_queue_pool = QueuePool()

    converter = JPGConverter(in_queue_pool, out_queue_pool)
    server = StreamServer(out_queue_pool)
    renderer = ImageRenderSetup(owner, converter, server)

    on_game_stop(owner, server.stop)
    on_game_stop(owner, converter.stop)

    renderer.run()
    converter.start()
    server.start()
