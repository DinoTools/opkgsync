opkgsync
========

[Opkg](https://code.google.com/p/opkg/) is a lightweight package management system. It is designed for embedded Linux devices and used in projects like [OpenWRT](https://openwrt.org/) and [OpenEmbedded](http://www.openembedded.org/).

The opkgsync tool provides an easy way to create a mirror of an opkg package repository. It has a very limited parser for 'Packages' files and can synchronize available packages to a local directory.

Requirements
------------

* Python >= 2.6
* Python >= 3.2

Install
-------

*Direct*:

Use the opkgsync.py file to synchronize the repository.

    chmod a+x opkgsync.py


Usage
-----

*Display help*:

    ./opkgsync.py --help

*Synchronize a repository*:

    ./opkgsync.py -vv -p http://example.org/generic/packages/Packages -d /local/package/repository

License
-------

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

