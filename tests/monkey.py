#
# Copyright 2012-2016 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license
#

from contextlib import contextmanager
from functools import wraps
import inspect


class Patch(object):

    def __init__(self, what):
        self.what = what
        self.old = []

    def apply(self):
        for module, name, that in self.what:
            old = getattr(module, name)
            self.old.append((module, name, old))
            # The following block is done so that if it is a method we are
            # patching in, that it will have the same type as the method it
            # replaced.
            if inspect.isclass(module):
                if inspect.isfunction(old):
                    that = staticmethod(that)
                elif (inspect.ismethod(old) and
                      getattr(old, 'im_self', None) is not None):
                    that = classmethod(that)
            setattr(module, name, that)

    def revert(self):
        assert self.old != []
        while self.old:
            module, name, that = self.old.pop()
            # The following block is only necessary for Python2 as it wrongly
            # sets the function as instancemethod instead of keeping it as
            # staticmethod.
            if inspect.isclass(module):
                if inspect.isfunction(that):
                    that = staticmethod(that)

            setattr(module, name, that)


@contextmanager
def patch_scope(what):
    patch = Patch(what)
    patch.apply()
    try:
        yield
    finally:
        patch.revert()


def patch_function(module, name, that):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kw):
            with patch_scope([(module, name, that)]):
                return f(*args, **kw)
        return wrapper
    return decorator


def patch_class(module, name, that):

    def setup_decorator(func):
        @wraps(func)
        def setup(self, *a, **kw):
            if not hasattr(self, '__monkeystack__'):
                self.__monkeystack__ = []
            patch = Patch([(module, name, that)])
            self.__monkeystack__.append(patch)
            patch.apply()
            return func(self, *a, **kw)
        return setup

    def teardown_decorator(func):
        @wraps(func)
        def teardown(self, *a, **kw):
            patch = self.__monkeystack__.pop()
            patch.revert()
            return func(self, *a, **kw)
        return teardown

    def wrapper(cls):
        cls.setUp = setup_decorator(cls.setUp)
        cls.tearDown = teardown_decorator(cls.tearDown)
        return cls

    return wrapper
