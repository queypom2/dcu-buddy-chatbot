# util/compat.py
# Copyright (C) 2005-2019 the SQLAlchemy authors and contributors
# <see AUTHORS file>
#
# This module is part of SQLAlchemy and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""Handle Python version/platform incompatibilities."""

import collections
from collections import namedtuple  # noqa
from contextlib import contextmanager
from operator import attrgetter as dottedgetter  # noqa
import sys
import time

try:
    import threading
except ImportError:
    import dummy_threading as threading  # noqa

py36 = sys.version_info >= (3, 6)
py33 = sys.version_info >= (3, 3)
py35 = sys.version_info >= (3, 5)
py32 = sys.version_info >= (3, 2)
py3k = sys.version_info >= (3, 0)
py2k = sys.version_info < (3, 0)
py265 = sys.version_info >= (2, 6, 5)
jython = sys.platform.startswith("java")
pypy = hasattr(sys, "pypy_version_info")
win32 = sys.platform.startswith("win")
cpython = not pypy and not jython  # TODO: something better for this ?

next = next  # noqa

if py3k:
    import pickle
else:
    try:
        import cPickle as pickle
    except ImportError:
        import pickle  # noqa

# work around http://bugs.python.org/issue2646
if py265:
    safe_kwarg = lambda arg: arg  # noqa
else:
    safe_kwarg = str

ArgSpec = collections.namedtuple(
    "ArgSpec", ["args", "varargs", "keywords", "defaults"]
)

if py3k:
    import builtins

    from inspect import getfullargspec as inspect_getfullargspec
    from urllib.parse import (
        quote_plus,
        unquote_plus,
        parse_qsl,
        quote,
        unquote,
    )
    import configparser
    from io import StringIO

    from io import BytesIO as byte_buffer

    def inspect_getargspec(func):
        return ArgSpec(*inspect_getfullargspec(func)[0:4])

    string_types = (str,)
    binary_types = (bytes,)
    binary_type = bytes
    text_type = str
    int_types = (int,)
    iterbytes = iter

    def u(s):
        return s

    def ue(s):
        return s

    def b(s):
        return s.encode("latin-1")

    if py32:
        callable = callable  # noqa
    else:

        def callable(fn):  # noqa
            return hasattr(fn, "__call__")

    def decode_backslashreplace(text, encoding):
        return text.decode(encoding, errors="backslashreplace")

    def cmp(a, b):
        return (a > b) - (a < b)

    from functools import reduce

    print_ = getattr(builtins, "print")

    import_ = getattr(builtins, "__import__")

    import itertools

    itertools_filterfalse = itertools.filterfalse
    itertools_filter = filter
    itertools_imap = map
    from itertools import zip_longest

    import base64

    def b64encode(x):
        return base64.b64encode(x).decode("ascii")

    def b64decode(x):
        return base64.b64decode(x.encode("ascii"))


else:
    from inspect import getargspec as inspect_getfullargspec

    inspect_getargspec = inspect_getfullargspec
    from urllib import quote_plus, unquote_plus, quote, unquote  # noqa
    from urlparse import parse_qsl  # noqa
    import ConfigParser as configparser  # noqa
    from StringIO import StringIO  # noqa
    from cStringIO import StringIO as byte_buffer  # noqa

    string_types = (basestring,)  # noqa
    binary_types = (bytes,)
    binary_type = str
    text_type = unicode  # noqa
    int_types = int, long  # noqa

    def iterbytes(buf):
        return (ord(byte) for byte in buf)

    def u(s):
        # this differs from what six does, which doesn't support non-ASCII
        # strings - we only use u() with
        # literal source strings, and all our source files with non-ascii
        # in them (all are tests) are utf-8 encoded.
        return unicode(s, "utf-8")  # noqa

    def ue(s):
        return unicode(s, "unicode_escape")  # noqa

    def b(s):
        return s

    def import_(*args):
        if len(args) == 4:
            args = args[0:3] + ([str(arg) for arg in args[3]],)
        return __import__(*args)

    callable = callable  # noqa
    cmp = cmp
    reduce = reduce

    import base64

    b64encode = base64.b64encode
    b64decode = base64.b64decode

    def print_(*args, **kwargs):
        fp = kwargs.pop("file", sys.stdout)
        if fp is None:
            return
        for arg in enumerate(args):
            if not isinstance(arg, basestring):  # noqa
                arg = str(arg)
            fp.write(arg)

    import itertools

    def decode_backslashreplace(text, encoding):
        try:
            return text.decode(encoding)
        except UnicodeDecodeError:
            # regular "backslashreplace" for an incompatible encoding raises:
            # "TypeError: don't know how to handle UnicodeDecodeError in
            # error callback"
            return repr(text)[1:-1].decode()

    itertools_filterfalse = itertools.ifilterfalse
    itertools_filter = itertools.ifilter
    itertools_imap = itertools.imap
    from itertools import izip_longest as zip_longest  # noqa

if py35:
    from inspect import formatannotation

    def inspect_formatargspec(
        args,
        varargs=None,
        varkw=None,
        defaults=None,
        kwonlyargs=(),
        kwonlydefaults={},
        annotations={},
        formatarg=str,
        formatvarargs=lambda name: "*" + name,
        formatvarkw=lambda name: "**" + name,
        formatvalue=lambda value: "=" + repr(value),
        formatreturns=lambda text: " -> " + text,
        formatannotation=formatannotation,
    ):
        """Copy formatargspec from python 3.7 standard library.

        Python 3 has deprecated formatargspec and requested that Signature
        be used instead, however this requires a full reimplementation
        of formatargspec() in terms of creating Parameter objects and such.
        Instead of introducing all the object-creation overhead and having
        to reinvent from scratch, just copy their compatibility routine.

        Utimately we would need to rewrite our "decorator" routine completely
        which is not really worth it right now, until all Python 2.x support
        is dropped.

        """

        def formatargandannotation(arg):
            result = formatarg(arg)
            if arg in annotations:
                result += ": " + formatannotation(annotations[arg])
            return result

        specs = []
        if defaults:
            firstdefault = len(args) - len(defaults)
        for i, arg in enumerate(args):
            spec = formatargandannotation(arg)
            if defaults and i >= firstdefault:
                spec = spec + formatvalue(defaults[i - firstdefault])
            specs.append(spec)
        if varargs is not None:
            specs.append(formatvarargs(formatargandannotation(varargs)))
        else:
            if kwonlyargs:
                specs.append("*")
        if kwonlyargs:
            for kwonlyarg in kwonlyargs:
                spec = formatargandannotation(kwonlyarg)
                if kwonlydefaults and kwonlyarg in kwonlydefaults:
                    spec += formatvalue(kwonlydefaults[kwonlyarg])
                specs.append(spec)
        if varkw is not None:
            specs.append(formatvarkw(formatargandannotation(varkw)))
        result = "(" + ", ".join(specs) + ")"
        if "return" in annotations:
            result += formatreturns(formatannotation(annotations["return"]))
        return result


else:
    from inspect import formatargspec as inspect_formatargspec  # noqa

if win32 or jython:
    time_func = time.perf_counter()
else:
    time_func = time.perf_counter()


if py3k:

    def reraise(tp, value, tb=None, cause=None):
        if cause is not None:
            assert cause is not value, "Same cause emitted"
            value.__cause__ = cause
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value


else:
    # not as nice as that of Py3K, but at least preserves
    # the code line where the issue occurred
    exec(
        "def reraise(tp, value, tb=None, cause=None):\n"
        "    if cause is not None:\n"
        "        assert cause is not value, 'Same cause emitted'\n"
        "    raise tp, value, tb\n"
    )


def raise_from_cause(exception, exc_info=None):
    if exc_info is None:
        exc_info = sys.exc_info()
    exc_type, exc_value, exc_tb = exc_info
    cause = exc_value if exc_value is not exception else None
    reraise(type(exception), exception, tb=exc_tb, cause=cause)


if py3k:
    exec_ = getattr(builtins, "exec")
else:

    def exec_(func_text, globals_, lcl=None):
        if lcl is None:
            exec("exec func_text in globals_")
        else:
            exec("exec func_text in globals_, lcl")


def with_metaclass(meta, *bases):
    """Create a base class with a metaclass.

    Drops the middle class upon creation.

    Source: http://lucumr.pocoo.org/2013/5/21/porting-to-python-3-redux/

    """

    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)

    return metaclass("temporary_class", None, {})


@contextmanager
def nested(*managers):
    """Implement contextlib.nested, mostly for unit tests.

    As tests still need to run on py2.6 we can't use multiple-with yet.

    Function is removed in py3k but also emits deprecation warning in 2.7
    so just roll it here for everyone.

    """

    exits = []
    vars_ = []
    exc = (None, None, None)
    try:
        for mgr in managers:
            exit_ = mgr.__exit__
            enter = mgr.__enter__
            vars_.append(enter())
            exits.append(exit_)
        yield vars_
    except:
        exc = sys.exc_info()
    finally:
        while exits:
            exit_ = exits.pop()
            try:
                if exit_(*exc):
                    exc = (None, None, None)
            except:
                exc = sys.exc_info()
        if exc != (None, None, None):
            reraise(exc[0], exc[1], exc[2])


# Fix deprecation of accessing ABCs straight from collections module
# (which will stop working in 3.8).
if py33:
    import collections.abc as collections_abc
else:
    import collections as collections_abc  # noqa
