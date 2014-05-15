#!/usr/bin/python3
# -*- mode: python; coding: utf-8 -*-

from distutils.core import setup

setup(
    name = 'insight',
    version = '0.140514',
    packages = ['insight'],

    author = "Oscar Acena",
    author_email = "oscaracena@gmail.com",
    url = "https://bitbucket.org/arco_group/insight",
    download_url = "https://bitbucket.org/arco_group/insight/get/tip.tar.gz",
    keywords = "blender streaming mjpeg".split(),
    description = "Make streaming of your Blender cameras",

    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Graphics :: 3D Rendering",
        "Topic :: Multimedia :: Graphics :: Capture",
        "Topic :: Multimedia :: Video :: Display",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],

    long_description = """\
Insight is a Python module that gives you the ability to stream the
content of any camera in your scene. It is designed for Blender Game
Engine.

Read the documentation on the web page for more information.
""",
)

