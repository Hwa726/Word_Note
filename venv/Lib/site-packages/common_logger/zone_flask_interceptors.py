# coding=utf8
"""
注1:
    trace日志一般来说，整体分为callee和caller两种，callee的意义是 本模块的 请求入口 和 请求出口 trace日志
    简单说，就是你开放了一个接口，那么一个访问进接口的时候打一条，出接口的时候打一条

注2:
    如果你使用的是flask框架，那么这个py会帮助你打印出来 callee日志

注3:
    callee日志包括 _com_request_in 和 _com_request_out日志

注4:
    该py文件适用的版本是 Flask 0.12.2  其他版本，需要实测
"""

from flask import request
import json
from Utils.LogUtils.util.thread_local_util import *
from Utils.LogUtils.base_trace_log import *
import Utils.LogUtils.common_logger
import traceback


def request_in_log():
    try:
        """
        prepare param
        """
        # 首先设置start_time进入栈区
        set_request_in_start_time()
        # 头信息取traceid和spanid
        headers = request.headers if hasattr(request, 'headers') else {}
        # if 'Didi-Header-Rid' in headers.keys():
        #     traceid = str(headers['Didi-Header-Rid'])
        #     set_traceid(traceid)
        # else:
        #     reset_traceid()
        # if 'Didi-Header-Spanid' in headers.keys():
        #     spanid = str(headers['Didi-Header-Spanid'])
        #     set_spanid(spanid)
        # else:
        #     reset_spanid()
        if 'Content-Type' in headers.keys():
            content_type = headers['Content-Type']
        else:
            content_type = ''

        referrer = str(request.referrer)
        remote_addr = str(request.remote_addr)
        url = str(request.url)
        uri = str(request.path)
        method = str(request.method)
        args = json.dumps(request.values)
        body = str(request.data)

        """
        log request in 
        """
        standard_log_request_in(
            uri=uri,
            url=url,
            referrer=referrer,
            remote_addr=remote_addr,
            args=args,
            body=body,
            content_type=content_type,
            method=method
        )
    except Exception as e:
        common_logger.pylogerror(traceback.format_exc(limit=1))
        pass


def normal_request_out_log(response):
    if response:
        try:
            """
            prepare param
            """
            referrer = str(request.referrer)
            remote_addr = str(request.remote_addr)
            url = str(request.url)
            uri = str(request.path)
            method = str(request.method)
            args = json.dumps(request.values)
            """
            log request out
            """
            end_time = time.time()
            proc_time = end_time - get_request_in_start_time()
            status_code = response.status_code
            # response里面的content内容
            content = response.response
            reason = response.status
            standard_log_request_out(
                uri=uri,
                errno=status_code,
                errmsg=reason,
                proc_time=proc_time,
                is_success=True if int(status_code) == 200 else False,
                referrer=referrer,
                remote_addr=remote_addr,
                url=url,
                method=method,
                args=args,
                response=content
            )
            clear_request_in_start_time()
        except Exception as e:
            common_logger.pylogerror(traceback.format_exc(limit=1))
            clear_request_in_start_time()
            pass
    return response


def exception_request_out_log(exception):
    if exception:
        try:
            """
            prepare param
            """
            referrer = str(request.referrer)
            remote_addr = str(request.remote_addr)
            url = str(request.url)
            uri = str(request.path)
            method = str(request.method)
            args = json.dumps(request.values)
            """
            log error request out
            """
            end_time = time.time()
            proc_time = end_time - get_request_in_start_time()
            status_code = 500
            # response里面的content内容
            content = None
            reason = exception
            standard_log_request_out(
                uri=uri,
                errno=status_code,
                errmsg=reason,
                proc_time=proc_time,
                is_success=True if int(status_code) == 200 else False,
                response=content,
                referrer=referrer,
                remote_addr=remote_addr,
                url=url,
                method=method,
                args=args
            )
            clear_request_in_start_time()
        except Exception as e:
            common_logger.pylogerror(traceback.format_exc(limit=1))
            clear_request_in_start_time()
            pass
