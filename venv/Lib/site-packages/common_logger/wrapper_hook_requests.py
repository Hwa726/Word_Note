# coding=utf8

"""
注1:
    该py是wrapper_http_sample.py的扩展
    因为wrapper_http_sample.py在实际使用的时候，需要修改部分代码，来适应你的http client，打出正确的http caller日志

注2:
    如果你的http请求是用的 requests 包，可以尝试使用这个py文件，配合wrapper_hook.py
    就不用修改任何一处代码，即可打出 http caller的日志(dltag = _com_http_success _com_http_failure)

注3:
    目前支持requests  2.18.4  其他版本，需要实测

注4:
    使用方式:
    (1)打开 wrapper_hook 里面的注释
    (2)在 import requests的上方 import wrapper_hook 即可
"""

import functools
import time
from Utils.LogUtils.base_trace_log import *
import traceback


# 根据 kwargs 拿到 get or post
def requests_init_getorpost(kwargs):
    method = ''
    if 'method' in kwargs:
        method = kwargs['method']
    return method


# 拿到url
def requests_init_url(kwargs):
    url = ''
    if 'url' in kwargs:
        url = kwargs['url']
    return url


# 拿到请求参数
def requests_init_args(kwargs):
    params_and_data = ''
    # get args
    if 'params' in kwargs:
        _temp_params = kwargs['params']
        _temp_params = str(_temp_params)
        params_and_data += _temp_params
    # post args
    if 'data' in kwargs:
        _temp_data = kwargs['data']
        _temp_data = str(_temp_data)
        params_and_data += _temp_data
    return params_and_data


# 设置请求头
def alternate_header(kwargs):
    if 'headers' not in kwargs:
        kwargs['headers'] = {}
    trace_struct = {
        'didi-header-rid': '',
        'didi-header-spanid': ''
    }
    # python http headers must be dict
    if not isinstance(kwargs['headers'], dict):
        return
    kwargs['headers'].update(trace_struct)


# requests 发起请求之前，提取请求参数，并且设置请求头
def prepare_params(kwargs):
    get_or_post = ''
    http_params = ''
    url = ''
    try:
        # create cspanid
        # cspanid = ''
        # put cspanid in thread local
        # set_cspanid(cspanid)

        # init_request_element
        url = requests_init_url(kwargs)
        http_params = requests_init_args(kwargs)
        get_or_post = requests_init_getorpost(kwargs)
        # alternate_header
        alternate_header(kwargs)
    except Exception as e:
        # do not clear cspanid
        common_logger.pylogerror(traceback.format_exc(limit=1))
        pass

    return get_or_post, http_params, url


# 打印正常请求的http trace日志
def log_normal_trace(
        get_or_post,
        http_params,
        response,
        start_time,
        url):
    # 打印trace http日志
    try:
        content = response.content
        reason = response.reason
        status_code = response.status_code
        end_time = time.time()
        proc_time = end_time - start_time
        standard_log_http(url=url,
                          proc_time=proc_time,
                          errno=status_code,
                          errmsg=reason,
                          is_success=True if int(status_code) == 200 else False,
                          response=content,
                          method=get_or_post,
                          args=http_params)


    except Exception as e:

        common_logger.pylogerror(traceback.format_exc(limit=1))
        pass


# 打印错误请求的http trace日志
def log_error_trace(e, http_params, start_time, url):
    try:
        end_time = time.time()
        proc_time = end_time - start_time
        standard_log_http(url=url,
                          proc_time=proc_time,
                          errno=500,  # 用户可以自己定义
                          errmsg=e.message,
                          is_success=False,
                          response=None,
                          args=http_params
                          )
    except Exception as e:
        # clear cspanid
        common_logger.pylogerror(traceback.format_exc(limit=1))
        pass


def requests_http_wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        """
        prepare params
        """
        get_or_post, http_params, url = prepare_params(kwargs)
        try:
            response = func(*args, **kwargs)
            """
            log normal trace
            """
            log_normal_trace(get_or_post, http_params, response, start_time, url)
            return response
        except Exception as e:
            """
            log error trace
            """
            log_error_trace(e, http_params, start_time, url)
            # must raise exception
            raise e

    return wrapper
