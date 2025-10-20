# coding=utf8

import traceback

import time

try:
    import cStringIO
except ImportError:
    import io as cStringIO

import sys


class SelfFormatter(object):
    converter = time.localtime

    def __init__(self, fmt=None, datefmt=None):

        if fmt:
            self._fmt = fmt
        else:
            self._fmt = "%(message)s"
        self.datefmt = datefmt

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            t = time.strftime("%Y-%m-%dT%H:%M:%S", ct)
            zone = time.strftime("%z", ct)
            s = "%s.%03d%s" % (t, record.msecs, zone)
        return s

    def formatException(self, ei):

        sio = cStringIO.StringIO()
        traceback.print_exception(ei[0], ei[1], ei[2], None, sio)
        s = sio.getvalue()
        sio.close()
        if s[-1:] == "\n":
            s = s[:-1]
        return s

    def usesTime(self):
        return self._fmt.find("%(asctime)") >= 0

    def format(self, record):
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self._fmt % record.__dict__
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            try:
                s = s + record.exc_text
            except UnicodeError:
                s = s + record.exc_text.decode(sys.getfilesystemencoding(),
                                               'replace')
        return s
