#!/usr/bin/env python
# opkgsync - Sync opkg package repositories
# Copyright (C) 2013 Philipp Seidel (DinoTools)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

"""
The opkgsync tool provides an easy way to create a mirror of an opkg package
repository. It has a very limited parser for 'Packages' files and can
synchronize available packages to a local directory.
"""

import logging
import os
import sys
from optparse import OptionParser
import hashlib
import tempfile

if sys.version_info[0] == 3:
    from urllib.parse import urlparse, urljoin
    from http.client import HTTPConnection
else:
    from urlparse import urlparse, urljoin
    from httplib import HTTPConnection


required_values = ["package", "filename", "size", "md5sum"]
compare_values = ["filename"]
log = logging.getLogger("opkgsync")


def get_filehash(filename, hashname="md5"):
    """
    Read a file and generate the hash.

    :param String filename: Name of the file
    :param String hashname: Name of the hash
    :return: Hash as Hex-String

    """
    h = hashlib.new(hashname)
    fp = open(filename, "rb")

    while True:
        d = fp.read(4096)
        if not d:
            break
        h.update(d)

    fp.close()
    return h.hexdigest()


def extract_information(stream):
    """
    Extract packages from a stream.

    :param stream: File pointer
    :return: List of packages with information

    """
    log.info("Extracting package information from stream ...")
    pkg_info = None
    pkgs = {}
    for line in stream.readlines():
        line = line.strip()
        try:
            # all information should be in ascii format
            line = line.decode('ascii')
        except BaseException:
            continue
        if line == "":
            if pkg_info is None:
                continue

            pkg_name = pkg_info.get("package", None)
            if pkg_name is not None and pkg_name != "":
                pkgs[pkg_name] = pkg_info
            else:
                pass
                # TODo: print error
            pkg_info = None
            continue

        key, sep, value = line.partition(": ")
        key = key.strip().lower()
        value = value.strip()

        if value == '':
            continue

        if key not in required_values:
            continue

        if pkg_info is None:
            pkg_info = {}

        pkg_info[key] = value

    return pkgs


def get_local_packages(download_path):
    """
    Read a local Packages file, extract packages and validate local files.

    :param String download_path: Path to download files to
    :return: Dict containing all packages

    """
    log.info("Preparing for local package information ...")
    pkgs = {}
    pkg_info_file = os.path.join(download_path, "Packages")
    if not os.path.isfile(pkg_info_file) or not os.access(pkg_info_file, os.R_OK):
        return pkgs

    fp = open(pkg_info_file, "rb")
    pkgs = extract_information(fp)
    fp.close()
    # create key list, because its not allowed to modify a dict while iterating
    pkg_names = list(pkgs.keys())
    for pkg_name in pkg_names:
        pkg = pkgs[pkg_name]
        pkg_filename = os.path.join(download_path, pkg.get("filename"))
        if not os.path.isfile(pkg_filename):
            pkgs.pop(pkg_name, None)
            continue

        file_size = os.path.getsize(pkg_filename)
        pkg_size = pkg.get("size", None)
        if pkg_size is None:
            pkg["size"] = file_size
            pkg_size = file_size
        if int(pkg_size) != file_size:
            pkgs.pop(pkg_name, None)
            continue

        file_md5 = get_filehash(pkg_filename)
        pkg_md5 = pkg.get("md5sum", None)
        if pkg_md5 is None:
            pkg["md5sum"] = file_md5
            pkg_md5 = file_md5
        if pkg_md5 != file_md5:
            pkgs.pop(pkg_name, None)
            continue

    return pkgs


def compare_pkg(pkg1, pkg2):
    """
    Compare pkg information.

    :param Dict pkg1: First package
    :param Dict pkg2: Second package
    :return: True = Packages are equal | False = Packages are not equal

    """
    for key in compare_values:
        if key not in pkg1:
            return False
        if key not in pkg2:
            return False
        if pkg1[key] != pkg2[key]:
            return False
    return True


def merge_pkg_lists(l1, l2):
    """
    Merge two package lists.

    It returns a Dict containing tuples.

    :param Dict l1: First package list
    :param Dict l2: Second package list
    :return: Dict of tuples

    """
    log.info("Merging package lists ...")
    pkgs = {}

    l1_keys = l1.keys()
    l2_keys = l2.keys()
    for pkg_name, pkg in l1.items():
        if pkg_name not in l2_keys:
            pkgs[pkg_name] = (pkg, None)
            continue
        pkgs[pkg_name] = (pkg, l2[pkg_name])

    for pkg_name, pkg in l2.items():
        if pkg_name in l1_keys:
            continue
        pkgs[pkg_name] = (None, pkg)

    return pkgs


def process_pkgs(pkgs):
    """
    Process package list and create a list of filenames to download.

    :param Dict pkgs: List of packages generated by merge_pkg_lists()
    :return: List of filenames

    """
    log.info("Processing %d packages ...", len(pkgs))
    files = []
    for pkg in pkgs.values():
        if pkg[0] is None and pkg[1] is None:
            continue
        if pkg[1] is None:
            os.remove(pkg[0]['filename'])
        elif pkg[0] is None:
            files.append(pkg[1]['filename'])
        elif not compare_pkg(pkg[0], pkg[1]):
            files.append(pkg[1]['filename'])
    return files


def download_files(files, url, download_path, conn=None):
    """
    Download all given files.

    :param List files: List of filenames
    :param url: URL-Object created with urlparse()
    :param String download_path: Path to download new files to
    :param conn: Connection to HTTP-Server

    """
    file_count = len(files)
    log.info("Downloading %d files ...", file_count)
    if conn is None:
        conn = HTTPConnection(url.netloc)

    for i, filename in enumerate(files, 1):
        log.debug("Downloading file(%d of %d) '%s' ...",
                  i, file_count, filename)
        conn.request("GET", urljoin(url.path, filename))
        response = conn.getresponse()
        fp = open(os.path.join(download_path, filename), "wb")
        data = response.read(1024)
        while data:
            fp.write(data)
            data = response.read(1024)
        fp.close()
        response.close()


def main():
    """Do the main processing."""

    parser = OptionParser()
    parser.add_option("-d", "--download_path", dest="download_path",
                      help="Path to download packages to "
                           "(defaults to local directory)",
                      metavar="PATH", default=".")
    parser.add_option("-p", "--packages_url", dest="packages_url",
                      help="URL of the Packages file", metavar="URL")
    parser.add_option("-v", dest="verbosity", default=0,
                      help="Verbosity", action="count")
    (options, args) = parser.parse_args()

    # init logger
    lvl = logging.ERROR - options.verbosity * 10
    if lvl < 0:
        lvl = 0
    logging.basicConfig(
        format='%(asctime)-15s [%(levelname)-8s] %(message)s',
        level=lvl
    )

    url = urlparse(options.packages_url)

    # fetch Packages from remote URL
    log.info("Fetching 'Packages' from remote Server ...")
    conn = HTTPConnection(url.netloc)
    conn.request("GET", url.path)
    response = conn.getresponse()
    # Cache remote 'Packages' file
    fp_tmp = tempfile.TemporaryFile(dir=options.download_path)
    data = response.read(4096)
    while data:
        fp_tmp.write(data)
        data = response.read(4096)
    fp_tmp.seek(0)

    # extract information
    remote_pkgs = extract_information(fp_tmp)
    local_pkgs = get_local_packages(options.download_path)

    # process local and remote package list
    pkgs = merge_pkg_lists(local_pkgs, remote_pkgs)
    files = process_pkgs(pkgs)

    # download files
    download_files(files, url, options.download_path, conn=conn)

    # write new file 'Packages'
    log.info("Writing local 'Packages' file ...")
    fp = open(os.path.join(options.download_path, "Packages"), "wb")
    fp_tmp.seek(0)
    data = fp_tmp.read(4096)
    while data:
        fp.write(data)
        data = fp_tmp.read(4096)
    fp.close()
    response.close()


if __name__ == "__main__":
    main()
