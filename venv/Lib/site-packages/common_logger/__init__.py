# coding=utf8
import os
import functools
from inspect import getframeinfo, stack
from .util.log_format import *
from .util.log_rotate_handler import *
from .model.normal_log_content import *
from .util.at_fork import monkeypatch_os_fork_functions

"""
该py提供logger的初始化，以及公用打日志方法
功能增加：
    1、日志增加调用函数位置所在文件名称及行数
    2、覆盖覆盖SQLAlchemy日志，统一格式
"""

loggers = {}

# 多进程环境下,fix logging
# 1.os.fork 添加wrapper
# 出现os.fork的地方，会增加wrapper的回调
monkeypatch_os_fork_functions()

import logging
import logging.handlers


# 2.hook logging
# 对于logging,出现os.fork的时候，增加3个回调
# 以保证fork子进程之后,handler.lock是释放的状态
# fix_logging_module()


# 注1:file_path 路径需要确认存在，组件不做"初始化系统文件夹操作"(因涉及os chmod相关)
# 注2:file_name自定义，一般与系统业务相关
# 注3:logger的name是'pylog',不需要修改
# 注4:is_need_console False代表不在控制台输出,True代表在控制台输出，True的时候一般用于调试，发布到线上的时候要关闭
# 注5:backupCount表示保留个数,比如rotate_type=MIDNIGHT,backupCount=10,则表示保存10天的数据
# 注6:rotate_type表示滚动形式，请选择 'H' 和 'MIDNIGHT'，不要选择其他形式
def init_logger(file_path='./',
                file_name='common_logger',
                is_need_console=True,
                console_level='DEBUG',
                backupCount=10,
                rotate_type='MIDNIGHT',
                log_level='DEBUG'
                ):
    # 记录业务日志问题
    file_logger(file_path,
                file_name,
                logger_name='pylog',
                is_need_console=is_need_console,
                backupCount=backupCount,
                rotate_type=rotate_type,
                console_level=console_level,
                log_level=log_level
                )
    # 覆盖SQLAlchemy日志格式
    file_logger(file_path,
                file_name,
                logger_name='sqlalchemy.engine.base.Engine',
                is_need_console=False,
                backupCount=backupCount,
                rotate_type=rotate_type,
                console_level=console_level,
                log_level=log_level
                )
    ## 记录组件本身遇到的问题
    ## 如果 z_pyhelper开头的日志文件里面有内容，请联系本组件开发者
    file_logger(file_path,
                "z_pyhelper",  # 以这个名称开头的日志文件，非业务错误，是日志组件自己打印的error信息
                logger_name="z_pyhelper",
                is_need_console=is_need_console,
                backupCount=backupCount,
                rotate_type=rotate_type,
                log_level='INFO'
                )


# 以日志文件形式，打印日志
def file_logger(file_path, file_name,
                logger_name='pylog',
                is_need_console=False,
                console_level='DEBUG',
                backupCount=10,
                rotate_type='MIDNIGHT',
                log_level='DEBUG'):
    """
    :param file_path:
    :param file_name:
    :param logger_name:
    :param is_need_console:
    :param backupCount:
    :param rotate_type:
    :param Level:
    :return:
    """
    global loggers
    if loggers.get(logger_name):
        return loggers.get(logger_name)
    else:

        logger = logging.getLogger(logger_name)

        # 设定日志等级为INFO
        logger.setLevel(logging.getLevelName(log_level))

        # formatter制定
        # 覆盖SQLAlchemy的内置logger
        if logger_name == 'sqlalchemy.engine.base.Engine':
            formatter = SelfFormatter("[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d]%(message)s")
        else:
            formatter = SelfFormatter("[%(levelname)s][%(asctime)s][%(d_filename)s:%(d_lineno)d]%(message)s")

        # handler 使用时间滚动的rotater
        if is_need_console:
            init_console_handler(logger, formatter, console_level)

        # info及以下级别的打到 .log文件 ,
        # warn和error日志打到 .log.wf文件中
        info_handler, error_handler = init_file_handler(file_path, file_name, formatter, backupCount, rotate_type)

        logger.addHandler(info_handler)
        logger.addHandler(error_handler)

        # 禁用传播
        # 该logger的日志，不会传播到root, logger内部的handler处理一切逻辑
        # root logger 有些web框架会导致日志重复
        logger.propagate = False

        loggers.update({logger_name: logger})
        return logger


# 打到console的handler
def init_console_handler(logger, formatter, console_level):
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.getLevelName(console_level))
    logger.addHandler(console_handler)


def init_file_handler(file_path, file_name, formatter, backupCount, rotate_type):
    # 打info及以下日志(如debug)
    class INFO_Level_Filter(logging.Filter):
        def filter(self, record):
            return record.levelno <= logging.INFO

    # 打info以上日志(如error)
    class WARN_Level_Filter(logging.Filter):
        def filter(self, record):
            return record.levelno > logging.INFO

    info_filename = file_path + "/" + file_name + ".log"
    error_filename = file_path + "/" + file_name + ".log.wf"

    # 使用MIDNIGHT 不使用 D
    # 注意 TimedRotatingFileHandler 是非进程安全的,禁止在线上环境中执行
    info_handler = SelfRotatingFileHandler(info_filename, when=rotate_type, interval=1, backupCount=backupCount)
    info_handler.setFormatter(formatter)
    info_handler.setLevel(logging.INFO)
    info_handler.addFilter(INFO_Level_Filter())

    error_handler = SelfRotatingFileHandler(error_filename, when=rotate_type, interval=1, backupCount=backupCount)
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.INFO)
    error_handler.addFilter(WARN_Level_Filter())
    return info_handler, error_handler


def get_root_logger():
    logger = loggers.get('pylog')
    return logger


def debug(msg, *args, **kwargs):
    caller = getframeinfo(stack()[1][0])
    if kwargs:
        if kwargs.get('extra', 0):
            kwargs['extra'].update({'d_filename': 1, 'd_lineno': 2})
        else:
            kwargs.update(extra={'d_filename': 1, 'd_lineno': 2})
    else:
        kwargs = dict(extra={'d_filename': caller.filename, 'd_lineno': caller.lineno})
    get_root_logger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    caller = getframeinfo(stack()[1][0])
    if kwargs:
        if kwargs.get('extra', 0):
            kwargs['extra'].update({'d_filename': caller.filename, 'd_lineno': caller.lineno})
        else:
            kwargs.update(extra={'d_filename': caller.filename, 'd_lineno': caller.lineno})
    else:
        kwargs = dict(extra={'d_filename': caller.filename, 'd_lineno': caller.lineno})
    get_root_logger().info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    caller = getframeinfo(stack()[1][0])
    if kwargs:
        if kwargs.get('extra', 0):
            kwargs['extra'].update({'d_filename': caller.filename, 'd_lineno': caller.lineno})
        else:
            kwargs.update(extra={'d_filename': caller.filename, 'd_lineno': caller.lineno})
    else:
        kwargs = dict(extra={'d_filename': caller.filename, 'd_lineno': caller.lineno})
    get_root_logger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    caller = getframeinfo(stack()[1][0])
    if kwargs:
        if kwargs.get('extra', 0):
            kwargs['extra'].update({'d_filename': caller.filename, 'd_lineno': caller.lineno})
        else:
            kwargs.update(extra={'d_filename': caller.filename, 'd_lineno': caller.lineno})
    else:
        kwargs = dict(extra={'d_filename': caller.filename, 'd_lineno': caller.lineno})
    get_root_logger().warning(msg, *args, **kwargs)


def fatal(msg, *args, **kwargs):
    caller = getframeinfo(stack()[1][0])
    if kwargs:
        if kwargs.get('extra', 0):
            kwargs['extra'].update({'d_filename': caller.filename, 'd_lineno': caller.lineno})
        else:
            kwargs.update(extra={'d_filename': caller.filename, 'd_lineno': caller.lineno})
    else:
        kwargs = dict(extra={'d_filename': caller.filename, 'd_lineno': caller.lineno})
    get_root_logger().fatal(msg, *args, **kwargs)


# 组件logger
def get_pylog_logger():
    logger = loggers.get('z_pyhelper')
    return logger


# 组件问题打印
def pylogerror(obj):
    get_pylog_logger().error(obj)


def logging_wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            info('run start')
            start_time = time.time()
            func(*args, **kwargs)
            end_time = time.time()
            proc_time = end_time - start_time
            info(f'run success||proc_time={proc_time}')
        except Exception as e:
            error('run fail')
            raise e

    return wrapper

