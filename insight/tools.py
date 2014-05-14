# -*- mode: python; coding: utf-8 -*-

from multiprocessing import Queue
from queue import Full, Empty
import logging
import bpy
import bge

logging.basicConfig(format='[%(name)s] %(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger("Insight")


def get_owner():
    return bge.logic.getCurrentController().owner


def inject_owner(fn):
    def deco(*args, **kwargs):
        return fn(get_owner(), *args, **kwargs)
    return deco


def addprefix(name):
    return "insight." + name


class GameStopDetector(object):
    def __init__(self, owner, callback):
        self.name = str(owner.name)
        self.callbacks = []

        gsd = owner.get(addprefix('gsd'))
        if gsd:
            gsd.callbacks.append(callback)
            return

        self.callbacks.append(callback)
        owner[addprefix('gsd')] = self

    def __del__(self):
        for cb in self.callbacks:
            cb()


def on_game_stop(owner, callback):
    GameStopDetector(owner, callback)


class IPCIface(object):
    def __init__(self):
        self.ipc = Queue()

    def ipc_invoke(self, method, **kargs):
        self.ipc.put([method, kargs])

    def ipc_dispatch_message(self, msg):
        method = getattr(self, msg[0])
        method(**msg[1])

    def ipc_process(self):
        try:
            while True:
                msg = self.ipc.get_nowait()
                self.ipc_dispatch_message(msg)
        except Empty:
            pass


class QueuePool(object):
    def __init__(self, pool_len=10, queue_len=10):
        self.queues = [Queue(queue_len) for i in range(pool_len)]
        self.usage = [False for i in range(pool_len)]

    def get(self, index):
        return self.queues[index]

    def acquire(self):
        assert not all(self.usage), "Max limit of queues reached"
        for index, v in enumerate(self.usage):
            if not v:
                self.usage[index] = True
                return self.queues[index], index

    def release(self, queue):
        index = self.get_index(queue)
        if not self.usage[index]:
            return

        self.usage[index] = False
        self.empty_queue(queue)

    def get_index(self, queue):
        for i, q in enumerate(self.queues):
            if q == queue:
                return i
        raise IndexError("Unknown queue")

    def empty_queue(self, queue):
        while True:
            try:
                queue.get_nowait()
            except Empty:
                pass


class ImageRenderSetup(object):
    def __init__(self, owner, converter, streamer):
        self.owner = owner
        self.scene = bge.logic.getCurrentScene()

        self.converter = converter
        self.streamer = streamer
        self.in_queue_pool = self.converter.in_queue_pool
        self.out_queue_pool = self.converter.out_queue_pool
        self.cameras = {}

        ImageRenderSetup.instance = self

    @classmethod
    def add_frame(cls, **desc):
        assert getattr(cls, "instance", None) is not None
        self = cls.instance

        try:
            camera = self.get_camera_info(desc)
            camera['src'].put_nowait(desc['data'])
        except Full:
            pass

    def get_camera_info(self, desc):
        camera = self.cameras.get(desc['name'])

        if camera is None:
            camera = self.create_camera(desc)
        return camera

    def create_camera(self, desc):
        logger.debug(" new camera added: {0}".format(desc['name']))

        src, src_index = self.in_queue_pool.acquire()
        dst, dst_index = self.out_queue_pool.acquire()

        camera = dict(
            name = desc['name'],
            size = desc['size'],
            src = src,
            src_index = src_index,
            dst = dst,
            dst_index = dst_index,
        )

        self.cameras[desc['name']] = camera
        self.streamer.add_camera(camera)
        self.converter.add_camera(camera)
        return camera

    def run(self):
        camera_list = self.get_available_cameras()
        if not camera_list:
            logger.warning(" There are no cameras to control")
            return

        self.setup_scene()
        changes = self.setup_cameras(camera_list)

        if changes:
            self.scene.restart()

    def get_available_cameras(self):
        names = []
        for c in self.scene.cameras:
            names.append(c.name)

        ignore_list = self.owner.get('ignore')
        if ignore_list is not None:
            for n in map(str.strip, ignore_list.split(",")):
                if n in names:
                    logger.debug(" Ignoring camera '{0}' by user settings".format(n))
                    names.remove(n)

        if "__default__cam__" in names:
            names.remove("__default__cam__")
        return names

    def setup_scene(self):
        self.image_for_texture = addprefix("texture.image")
        if self.image_for_texture in bpy.data.images:
            return

        bpy.ops.image.new(
            name = self.image_for_texture,
            width = 512,
            height = 512,
            generated_type = "COLOR_GRID"
        )

    def setup_cameras(self, camera_list):
        changes = []
        for name in camera_list:
            changes.append(self.setup_camera(name))

        return any(changes)

    def setup_camera(self, name):
        plane_name = addprefix("display." + name)
        plane = bpy.data.objects.get(plane_name)
        if plane is not None:
            return False

        plane = self.new_display_plane(plane_name)
        self.add_display_texture(plane, name)
        self.add_imagerender_setup_controller(plane)
        self.add_imagerender_refresh_controller(plane)
        self.add_display_properties(plane, name)
        self.hide_object(plane)
        return True

    def new_display_plane(self, name):
        bpy.ops.mesh.primitive_plane_add(radius=0.1, location=(0, 0, 0))
        plane = bpy.context.object
        plane.name = name
        plane.parent = bpy.data.objects[self.owner.name]
        return plane

    def add_display_texture(self, plane, name):
        bpy.ops.mesh.uv_texture_add()
        mat = bpy.data.materials.new(addprefix("material." + name))
        text = bpy.data.textures.new(addprefix("texture." + name), type="IMAGE")
        text.image = bpy.data.images[self.image_for_texture]
        slot = mat.texture_slots.add()
        slot.texture = text
        slot.texture_coords = "UV"
        plane.data.materials.append(mat)

    def add_imagerender_setup_controller(self, plane):
        action_name = "setup_texture"

        bpy.ops.logic.controller_add(type="PYTHON", name=action_name, object=plane.name)
        controller = plane.game.controllers[-1]
        controller.mode = "MODULE"
        controller.module = "{}.{}".format(__name__, action_name)

        bpy.ops.logic.sensor_add(type="ALWAYS", name=action_name, object=plane.name)
        sensor = plane.game.sensors[-1]
        sensor.link(controller)

    def add_imagerender_refresh_controller(self, plane):
        action_name = "refresh_texture"

        bpy.ops.logic.controller_add(type="PYTHON", name=action_name, object=plane.name)
        controller = plane.game.controllers[-1]
        controller.mode = "MODULE"
        controller.module = "{}.{}".format(__name__, action_name)

        bpy.ops.logic.sensor_add(type="ALWAYS", name=action_name, object=plane.name)
        sensor = plane.game.sensors[-1]
        sensor.use_pulse_true_level = True
        sensor.link(controller)

    def add_display_properties(self, plane, name):
        bpy.ops.object.game_property_new(type='STRING', name="camera")
        plane.game.properties['camera'].value = name

        bpy.ops.object.game_property_new(type='BOOL', name="enabled")
        plane.game.properties['enabled'].value = False

    def hide_object(self, obj):
        obj.hide = True
        obj.hide_render = True
        obj.hide_select = True


@inject_owner
def setup_texture(owner):
    scene = bge.logic.getCurrentScene()
    camera = scene.cameras[owner['camera']]
    matname = "MA" + bpy.data.objects.get(owner.name).data.materials[0].name
    matid = bge.texture.materialID(owner, matname)

    texture = bge.texture.Texture(owner, matid)
    texture.source = bge.texture.ImageRender(scene, camera)
    texture.source.flip = True
    texture.source.capsize = (640, 480)
    owner['texture'] = texture


@inject_owner
def refresh_texture(owner):
    if not owner['enabled']:
        return

    try:
        texture = owner['texture']
        texture.refresh(True)
    except KeyError:
        return

    if texture.source.image is None:
        logger.warning("image is None")
        return

    ImageRenderSetup.add_frame(
        name = owner['camera'],
        size = texture.source.size,
        data = bytes(texture.source.image)
    )
