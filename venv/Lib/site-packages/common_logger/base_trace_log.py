# coding=utf8
from Utils.LogUtils.model.trace_content import TraceContent
from Utils.LogUtils.common_dltags import common_dltags
from Utils.LogUtils import common_logger



# standard request_in log
def standard_log_request_in(
        uri,
        **kwargs
):
    l = TraceContent()
    l.set_dltag(common_dltags['request_in'])
    message = kwargs if kwargs else {}
    message['uri'] = uri
    l.log_pairs(message)
    common_logger.info(l)
    return


# standard request_out log
def standard_log_request_out(
        uri,
        errno,
        errmsg,
        proc_time,
        is_success,  # 成功或者失败，用户可以自定义传入
        response=None,
        **kwargs
):
    if not response:
        response = {}
    l = TraceContent()
    l.set_dltag(common_dltags['request_out'])
    message = kwargs if kwargs else {}
    message.update({"uri": uri,
                    "errno": errno,
                    "errmsg": errmsg,
                    "proc_time": proc_time,
                    "response": response}
                   )
    l.log_pairs(message)
    if not is_success:
        common_logger.error(l)
    else:
        common_logger.info(l)
    return


# standard http log
def standard_log_http(
        url,
        proc_time,
        errno,
        errmsg,
        is_success,  # 成功或者失败，用户可以自定义传入
        response=None,
        **kwargs
):
    l = TraceContent()
    if not is_success:
        l.set_dltag(common_dltags['http_failure'])
    else:
        l.set_dltag(common_dltags['http_success'])
    message = kwargs if kwargs else {}
    message.update({"url": url,
                    "proc_time": proc_time,
                    "errno": errno,
                    "errmsg": errmsg,
                    "response": response}
                   )
    l.log_pairs(message)
    if not is_success:
        common_logger.error(l)
    else:
        common_logger.info(l)
    return


# standard thrift log
def standard_log_thrift(
        host,
        port,
        interface,
        proc_time,
        errno,
        errmsg,
        is_success,  # 成功或者失败，用户可以自定义传入
        response=None,
        **kwargs
):
    if not response:
        response = {}
    l = TraceContent()
    if not is_success:
        l.set_dltag(common_dltags['thrift_failure'])
    else:
        l.set_dltag(common_dltags['thrift_success'])
    message = kwargs if kwargs else {}
    message.update(
        {"host": host,
         "port": port,
         "interface": interface,
         "proc_time": proc_time,
         "errno": errno,
         "errmsg": errmsg,
         "response": response
         })
    l.log_pairs(message)
    if not is_success:
        common_logger.error(l)
    else:
        common_logger.info(l)
    return


# standard mysql log
def standard_log_mysql(
        host,
        port,
        proc_time,
        errno,
        errmsg,
        is_success,  # 成功或者失败，用户可以自定义传入
        sql='',
        **kwargs

):
    l = TraceContent()
    if not is_success:
        l.set_dltag(common_dltags['mysql_failure'])
    else:
        l.set_dltag(common_dltags['mysql_success'])
    message = kwargs if kwargs else {}
    message.update(
        {"host": host,
         "port": port,
         "proc_time": proc_time,
         "errno": errno,
         "errmsg": errmsg,
         "sql": sql
         })
    l.log_pairs(message)
    if not is_success:
        common_logger.error(l)
    else:
        common_logger.info(l)
    return


# standard redis log
def standard_log_redis(
        host,
        port,
        proc_time,
        errno,
        errmsg,
        is_success,  # 成功或者失败，用户可以自定义传入
        method='',
        **kwargs
):
    l = TraceContent()
    if not is_success:
        l.set_dltag(common_dltags['redis_failure'])
    else:
        l.set_dltag(common_dltags['redis_success'])
    message = kwargs if kwargs else {}
    message.update(
        {"host": host,
         "port": port,
         "proc_time": proc_time,
         "errno": errno,
         "errmsg": errmsg,
         "method": method
         })
    l.log_pairs(message)
    if not is_success:
        common_logger.error(l)
    else:
        common_logger.info(l)
    return


def common_trace_log(dltag, level_str, **kwargs):
    """
    1.打trace方式任意，不对KV做强制要求
    2.common的dltag不推荐使用这种方式,使用下列standard_log_*方法
    3.非common的dltag使用这种方式
    """
    if not kwargs:
        return
    l = TraceContent()
    l.set_dltag(dltag if dltag else '_undef')
    message = kwargs if kwargs else {}
    l.log_pairs(message)
    if level_str == 'info':
        common_logger.info(l)
    elif level_str == 'warn':
        common_logger.warning(l)
    else:
        common_logger.error(l)


# 仅改造格式,不添加trace结构体的日志
# 比如之前是logging.info(s),那么可以改造成为common_logger.info_normalstr(s)
def info_tracestr(s):
    if not s:
        return
    common_trace_log("_undef", "info", _msg=str(s))


def warn_tracestr(s):
    if not s:
        return
    common_trace_log("_undef", "warn", _msg=str(s))


def error_tracestr(s):
    if not s:
        return
    common_trace_log("_undef", "error", _msg=str(s))

# if __name__ == '__main__':
    # common_trace_log("_http_ok", 0)
    #
    # standard_log_request_in(uri='/path1', content_type="application-json",
    #                         args={}, method='GET', remote_ip='127.0.0.1',
    #                         host='localhost', errno=0, errmsg='ok')
    # standard_log_request_in(None)
    #
    # standard_log_request_out(uri="/123", errno=0, errmsg="ok", proc_time=0.1, is_success=True, response={}, args={},
    #                          test=(123, 456), t2={list: 123})
    #
    # standard_log_http(url='http://localhost:10001/tornado_a/first',
    #                   proc_time=0.01,
    #                   errno=500,
    #                   x="123",
    #                   errmsg='failed',
    #                   response={},
    #                   is_success=False, y=[])
#
#     # standard_log_redis(host='local',port=6379,proc_time=0.01,errno=0,errmsg='ok',is_success=1,command='hdel XXX')
#
#     dic = {}
#     dic.update(None)
#     print(dic)
