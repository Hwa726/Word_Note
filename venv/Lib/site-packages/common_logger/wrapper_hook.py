# coding=utf8

import functools
import importlib
import sys
import time

from Utils.LogUtils.wrapper_hook_requests import requests_http_wrapper

_hook_modules = {'requests'}


class MetaPathFinder:

    def find_module(self, fullname, path=None):
        if fullname in _hook_modules:
            return MetaPathLoader()


class MetaPathLoader:

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        '''
        先从 sys.meta_path 中删除自定义的 finder
        防止下面执行 import_module 的时候再次触发此 finder
        从而出现递归调用的问题
        '''
        finder = sys.meta_path.pop(0)
        # 导入 module
        module = importlib.import_module(fullname)

        module_hook(fullname, module)

        sys.meta_path.insert(0, finder)
        return module


def module_hook(fullname, module):
    if fullname == 'requests':
        # 植入 requests.sessions.Session.request
        module.sessions.Session.request = requests_http_wrapper(module.sessions.Session.request)


# 如需使用，请打开注释
# sys.meta_path.insert(0, MetaPathFinder())
