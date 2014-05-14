Description
-----------

Insight is a Python module that gives you the ability to stream the
content of any camera in your scene. It is designed for Blender Game
Engine.

A note on Blender version
-------------------------

This module is intended for use in a modified version of Blender
2.70. Why? The following is some kind of technical explanation.

There is a little "bug" (although it's not really a bug, just a
missing feature) on Blender up to the last release. The thing is that,
in Python, you cannot convert a bgl.Buffer to some sort of array (like
list, bytes or array) without copying the entire buffer. This is not
optimal. There is a little patch to solve it (you can see the details
here: https://developer.blender.org/D494)

This patch is submitted to be included in a future release of Blender,
but until then, applying the patch and compiling yourself is the only
solution. If someone asks me, I could upload a patched version
compiled for GNU/Linux of Blender 2.70.5.

I'll update this README as soon as the patch is accepted.

Installation
------------

This is a Python module. There should be many ways of installing
it. Please, choose one of the following.

# Using Python pip

As simple as ever:

	::shell
	$ sudo pip install insight

# Install from source

Download this repository, open a shell and enter the repository
directory. Then, just type the following:

	::shell
	$ sudo python3 setup.py install

Remember to use Python3, because is what Blender uses.

# Don't install, just use

You could just download this repo and set the ``PYTHONPATH``
environment variable correctly. Then, launch Blender in a way that
assures you that it will use this variable.

For example, if you download this repo on ``/home/user/insight``, you
should set the ``PYTHONPATH`` like this:

    ::shell
	$ export PYTHONPATH="/home/user/insight"

and, in the same shell, run blender afterwards.

Setting up
----------

It is very easy to add support for Insight in your scene. You just
need to do the following steps.

1. Add a Empty object to your scene (actually, no matter what kind of
object you use, but an Empty one is very suitable). You could hide it
if you want. Call it whatever make sense for you, for example,
*InsightController*.

![Add empty Object](https://bytebucket.org/arco_group/insight/raw/tip/doc/images/add_empty.png)
![Set name to empty Object](https://bytebucket.org/arco_group/insight/raw/tip/doc/images/name_empty.png)

2. In Logic Editor, select the Empty object and add a new *Always*
sensor. Do not set it to repeat.

2. Add a new *Python* controller, and connect both, the sensor and
this controller. Set *Execution Method* to *Module*, and point to
*insight.init*.

![Add sensor and controller](https://bytebucket.org/arco_group/insight/raw/tip/doc/images/add_controller.png)

Done! Just remains one detail: set the Viewport Shading of your view
to *textured*. This is very important.

![Set view to Textured](https://bytebucket.org/arco_group/insight/raw/tip/doc/images/object_mode.png)

Now, if you launch the Game Engine, it will create the needed elements
to make it work. It takes all the cameras in your scene, and makes
them available for streaming. By default, all cameras are
disabled. You can enable one by selecting the *display* plane created
by Insight, and setting the Game Property *enabled* to True (just
check the checkbox).

![Choose display for Camera](https://bytebucket.org/arco_group/insight/raw/tip/doc/images/select_display.png)

Using it
--------

Ok, I've done everything you said, but, where is the video? The answer
is simple: expecting you! Let me explain. Insight serves all videos as
MJPG streams. So, you need to connect a Video Player to the internal
Insight server.

The stream is available in all your network interfaces, on port 8080
by default. The name of the stream is the name of the camera. So, if
you have a camera called ``Kitchen``, then the video of your camera will
be available at http://127.0.0.1:8080/Kitchen

The easiest way to test this is using a web browser with support for
MJPG streams (like recent versions of Chrome or Safari).  Make a HTML
file and call it whatever you want, i.e ``cameras.html``. Put inside the
following code (modify according to your needs, specially the name of
the camera)

	::html
	<html>
	  <head>
	  </head>

	  <body style="background-color:#404040; text-align: center">
        <img src="http://127.0.0.1:8080/Kitchen/>
	  </body>

    </html>

You could use the file called ``15cameras.html`` in the examples
directory as a guide. Next, run the Blender Game Engine and open the
file with your browser. If everything is fine, you should see what your
camera does.

Troubleshooting
---------------

1. I get the message: ``ERROR:INVALID viewport/shade mode, set it to
TEXTURED`` or ``WARNING:image is None``. This is because your 3D view
is not in *textured* mode. Please, set it!

2. I see a 404 error on the console. The camera is not
available. Remember that you need to enable it in *Game Properties*.
