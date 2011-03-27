#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generic extension system.

Copyright (C) 2009 Florian Léger

Setup script.

License
=======
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see U{http://www.gnu.org/licenses/}.
"""

__author__ = "Florian Léger"
__license__ = "GPLv3"
__version__ = "1.0.0"
__date__ = "04/10/2009"
__copyright__ = "2009 Florian Léger"

from distutils.core import setup

setup(name = "pyAutoExtension",
    version = __version__,
    description = "Generic extension system.",
    author = __author__,
    author_email = "florian.leger@insa-rouen.fr",
    url = "http://asi.insa-rouen.fr/etudiants/~fleger",
    platforms = ['any'],

    license = __license__,

    package_dir = {'autoextension': 'autoextension'},
    packages = ['autoextension'],

    classifiers = [
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Development Status :: 5 - Production/Stable',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python'],
)

