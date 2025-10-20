# coding=utf8

import threading
import collections
from Utils.LogUtils.util.id_creator import SpanIdGenerator
import time

_thread_local = threading.local()

SpanContext = collections.namedtuple('SpanContext', ['traceid', 'spanid'])


def get_span_context():
    if not hasattr(_thread_local, 'span_context'):
        _thread_local.span_context = SpanContext(traceid='', spanid='')
    return _thread_local.span_context


def set_context(context):
    _thread_local.span_context = context


# same thread ,same traceid
def get_traceid():
    span_context = get_span_context()

    if not span_context.traceid:
        sg = SpanIdGenerator()
        trace_id = sg.create_trace_id()

        # use replace
        span_context = span_context._replace(traceid=trace_id)
        _thread_local.span_context = span_context
    return span_context.traceid


# same thread,same spanid
def get_spanid():
    span_context = get_span_context()
    if not span_context.spanid:
        sg = SpanIdGenerator()
        span_id = sg.create_span_id()

        # use replace
        span_context = span_context._replace(spanid=span_id)
        _thread_local.span_context = span_context
    return span_context.spanid


def clear_span_context():
    _thread_local.span_context = SpanContext(traceid='', spanid='')


#
def reset_traceid():
    sg = SpanIdGenerator()
    traceid = sg.create_trace_id()
    span_context = get_span_context()
    # use replace
    span_context = span_context._replace(traceid=traceid)
    _thread_local.span_context = span_context


def set_traceid(traceid):
    span_context = get_span_context()
    span_context = span_context._replace(traceid=traceid)
    _thread_local.span_context = span_context


def reset_spanid():
    sg = SpanIdGenerator()
    spanid = sg.create_span_id()
    span_context = get_span_context()
    # use replace
    span_context = span_context._replace(spanid=spanid)
    _thread_local.span_context = span_context


def set_spanid(spanid):
    span_context = get_span_context()
    span_context = span_context._replace(spanid=spanid)
    _thread_local.span_context = span_context


"""
cspanid
"""


def create_cspanid():
    sg = SpanIdGenerator()
    spanid = sg.create_span_id()
    return spanid


# get cspanid
# if has, get id ,else get ''
def get_cspanid():
    if not hasattr(_thread_local, 'cspanid'):
        _thread_local.cspanid = ''
    return _thread_local.cspanid


def set_cspanid(cspan_id):
    _thread_local.cspanid = cspan_id


def clear_cspanid():
    _thread_local.cspanid = ''


'''
start_time
在callee request 中使用
'''


def get_request_in_start_time():
    if not hasattr(_thread_local, 'request_in_start_time'):
        _thread_local.request_in_start_time = 0
    return _thread_local.request_in_start_time


def set_request_in_start_time():
    _thread_local.request_in_start_time = time.time()


def clear_request_in_start_time():
    _thread_local.request_in_start_time = 0
