#!/usr/bin/env python

from setuptools import setup

import opkgsync

setup(name="opkgsync",
      version="1.0",
      description="Tool to synchronize opkg repositories to local directory",
      long_description=opkgsync.__doc__,
      author="DinoTools",
      author_email="",
      url="https://github.com/DinoTools/opkgsync",
      py_modules=["opkgsync"],
      license="GPLv3",
      plattforms="any",
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.2",
          "Programming Language :: Python :: 3.3"],
      entry_points="""
          [console_scripts]
          opkgsync = opkgsync:main
          """
      )
