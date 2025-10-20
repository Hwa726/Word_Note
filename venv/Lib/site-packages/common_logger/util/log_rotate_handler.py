# coding=utf8
import os
import re
from logging.handlers import BaseRotatingHandler
import codecs
import time
from stat import ST_MTIME

from portalocker import lock, unlock, LOCK_EX

_PER_HOUR = 60 * 60  # 每小时的秒数
_MIDNIGHT = 24 * 60 * 60  # 每天秒数


class SelfRotatingFileHandler(BaseRotatingHandler):
    """
    Handler for logging to a file, rotating the log file at certain timed
    intervals.

    If backupCount is > 0, when rollover is done, no more than backupCount
    files are kept - the oldest ones are deleted.
    """

    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=0, utc=False):
        # 文件流是 a 操作
        # 初始化stream，但stream会随时关闭，所以emit的时候，确保stream的存在
        BaseRotatingHandler.__init__(self, filename, 'a', encoding, delay)
        self.when = when.upper()
        self.backupCount = backupCount
        self.utc = utc
        # Calculate the real rollover interval, which is just the number of
        # seconds between rollovers.  Also set the filename suffix used when
        # a rollover occurs.  Current 'when' events supported:
        # S - Seconds
        # M - Minutes
        # H - Hours
        # D - Days
        # midnight - roll over at midnight
        # W{0-6} - roll over on a certain day; 0 - Monday
        #
        # Case of the 'when' specifier is not important; lower or upper case
        # will work.
        if self.when == 'S':
            self.interval = 1  # one second
            self.suffix = "%Y%m%d%H%M%S"
            self.extMatch = r"^\d{4}\d{2}\d{2}\d{2}\d{2}\d{2}$"
        elif self.when == 'M':
            self.interval = 60  # one minute
            self.suffix = "%Y%m%d%H%M"
            self.extMatch = r"^\d{4}\d{2}\d{2}\d{2}\d{2}$"
        elif self.when == 'H':
            self.interval = 60 * 60  # one hour
            self.suffix = "%Y%m%d%H"
            self.extMatch = r"^\d{4}\d{2}\d{2}\d{2}$"
        elif self.when == 'D' or self.when == 'MIDNIGHT':
            self.interval = 60 * 60 * 24  # one day
            self.suffix = "%Y%m%d"
            self.extMatch = r"^\d{4}\d{2}\d{2}$"
        elif self.when.startswith('W'):
            self.interval = 60 * 60 * 24 * 7  # one week
            if len(self.when) != 2:
                raise ValueError("You must specify a day for weekly rollover from 0 to 6 (0 is Monday): %s" % self.when)
            if self.when[1] < '0' or self.when[1] > '6':
                raise ValueError("Invalid day specified for weekly rollover: %s" % self.when)
            self.dayOfWeek = int(self.when[1])
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}$"
        else:
            raise ValueError("Invalid rollover interval specified: %s" % self.when)

        # compile
        self.extMatch = re.compile(self.extMatch)
        self.interval = self.interval * interval  # multiply by units requested

        # filename是base_file
        if os.path.exists(filename):
            # 如果文件名存在,取最后修改时间
            t = os.stat(filename)[ST_MTIME]
        else:
            # 否则取当前时间
            t = int(time.time())
        self.rolloverAt = self.computeRollover(t)

        # stream_lock
        self.stream_lock = None

        # \n标识
        if not hasattr(self, "terminator"):
            self.terminator = "\n"

        # lock obj 取该 file.__lock的句柄
        self.lockFilename = self.getLockFilename()

    # lock file name
    def getLockFilename(self):
        if self.baseFilename.endswith(".log"):
            lock_file = self.baseFilename[:-4]
        else:
            lock_file = self.baseFilename
        lock_file += ".lock"
        return lock_file

    # 打开锁文件
    def _open_lockfile(self):
        if self.stream_lock and not self.stream_lock.closed:
            return
        lock_file = self.lockFilename
        self.stream_lock = open(lock_file, "wb", buffering=0)

    # 关闭super._open()
    # def _open(self, mode=None):
    #     # 用do_open()替代
    #     return None

    # _open替换为do_open，拿到open()的stream
    def do_open(self, mode=None):
        if mode is None:
            mode = self.mode
        if self.encoding is None:
            stream = open(self.baseFilename, mode)
        else:
            stream = codecs.open(self.baseFilename, mode, self.encoding)
        return stream

    # 关闭文件流，确保self.stream=None
    def _close(self):
        """ Close file stream.  Unlike close(), we don't tear anything down, we
        expect the log to be re-opened after rotation."""

        if self.stream:
            try:
                if not self.stream.closed:
                    # Flushing probably isn't technically necessary, but it feels right
                    self.stream.flush()
                    self.stream.close()
            finally:
                self.stream = None

    def flush(self):
        """Does nothing; stream is flushed on each write."""
        return

    # linux file lock
    def _do_lock(self):
        self._open_lockfile()
        if self.stream_lock:
            # linux file lock
            lock(self.stream_lock, LOCK_EX)

    # linux file unlock
    def _do_unlock(self):
        if self.stream_lock:
            unlock(self.stream_lock)
            self.stream_lock.close()
            self.stream_lock = None

    def close(self):
        """
        Close log stream and stream_lock. """
        try:
            self._close()
        finally:
            # 关闭文件流,有保证线程安全的操作
            super(SelfRotatingFileHandler, self).close()

    def do_write(self, msg):
        """确保emit()时，已经加了linux锁，且文件流打开"""
        self.stream = self.do_open()
        stream = self.stream
        stream.write(msg)
        if self.terminator:
            stream.write(self.terminator)
        stream.flush()
        self._close()
        return

    # 重写emit方法,不在acquire()与release()里面加入linux lock
    # acquiere()和require()已经加了线程锁
    # 所以这里加入 linux file lock
    # doRollover 和 write 都是单进程单线程操作
    def emit(self, record):
        try:
            msg = self.format(record)
            try:
                # 唯一进程锁锁操作
                self._do_lock()
                # print("emit", os.getpid(), threading.current_thread().ident, id(self.lock))
                try:
                    if self.shouldRollover(record):
                        self.doRollover()
                except Exception as e:
                    pass

                self.do_write(msg)

            finally:
                # 放进程锁
                self._do_unlock()
        except Exception:
            self.handleError(record)

    # 文件最后修改时间或当前时间
    def computeRollover(self, currentTime):

        result = currentTime + self.interval
        # Hour
        if self.when == 'H':
            t = time.localtime(currentTime)
            currentMinute = t[4]
            currentSecond = t[5]
            r = _PER_HOUR - (currentMinute * 60 +
                             currentSecond)
            result = currentTime + r

        # Day
        if self.when == 'MIDNIGHT' or self.when.startswith('W'):
            if self.utc:
                t = time.gmtime(currentTime)
            else:
                t = time.localtime(currentTime)
            currentHour = t[3]
            currentMinute = t[4]
            currentSecond = t[5]
            r = _MIDNIGHT - ((currentHour * 60 + currentMinute) * 60 +
                             currentSecond)
            result = currentTime + r

            if self.when.startswith('W'):
                day = t[6]  # 0 is Monday
                if day != self.dayOfWeek:
                    if day < self.dayOfWeek:
                        daysToWait = self.dayOfWeek - day
                    else:
                        daysToWait = 6 - day + self.dayOfWeek + 1
                    newRolloverAt = result + (daysToWait * (60 * 60 * 24))
                    if not self.utc:
                        dstNow = t[-1]
                        dstAtRollover = time.localtime(newRolloverAt)[-1]
                        if dstNow != dstAtRollover:
                            if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                                addend = -3600
                            else:  # DST bows out before next rollover, so we need to add an hour
                                addend = 3600
                            newRolloverAt += addend
                    result = newRolloverAt

        return result

    def shouldRollover(self, record):
        """
        Determine if rollover should occur.

        record is not used, as we are just comparing times, but it is needed so
        the method signatures are the same
        """
        t = int(time.time())
        # print("now  ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t)))
        # print("rolloverAt   "   ,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.rolloverAt)))
        if t >= self.rolloverAt:
            return 1
        # print "No need to rollover: %d, %d" % (t, self.rolloverAt)
        return 0

    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which just used glob.glob().
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        prefix = baseName + "."
        plen = len(prefix)
        for fileName in fileNames:
            if fileName[:plen] == prefix:
                suffix = fileName[plen:]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result

    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        # 1.初始化的时候，文件产生的文件流，先关闭,不再往文件中写了
        self._close()
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]  # 夏令时
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)

        # 2.单进程下rename
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        if not os.path.exists(dfn) and os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, dfn)

        # 3.单进程下处理backup
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)

        # 4.重新打开文件流
        self.mode = "a"
        self.stream = self.do_open()

        # 5.重新计算 rollover时间
        newRolloverAt = self.computeRollover(currentTime)

        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend

        # 6.rotate时间重置
        self.rolloverAt = newRolloverAt
