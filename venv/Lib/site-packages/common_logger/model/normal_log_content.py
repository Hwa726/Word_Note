# coding=utf8
import json


class NormalLogContent:

    def __init__(self):
        self.log_kvpairs = []
        self.dltag = '_undef'

    def set_cspanid(self, cspanid):
        self.cspanid = cspanid

    # no need key
    def log_no_pair(self, temp_str):
        self.log_kvpairs.append({'_msg': temp_str})

    # kv pair
    def log_pair(self, k, v):
        self.log_kvpairs.append({k: v})

    # kv pairs
    def log_pairs(self, dic):
        if not isinstance(dic, DictType):
            # throw exception
            raise Exception("not dict type", dic)

        for k in dic:
            self.log_kvpairs.append({k: dic[k]})

    def set_dltag(self, dltag):
        if not dltag:
            return
        self.dltag = dltag

    def __str__(self):
        temp_str = ' '
        temp_str += self.dltag + '||'
        for i in range(0, len(self.log_kvpairs)):
            temp_dict = self.log_kvpairs[i]
            (k, v), = temp_dict.items()
            if isinstance(v, dict):
                try:
                    v = json.dumps(v, encoding="UTF-8")
                except Exception as e:
                    v = v
            temp_str += str(k) + '=' + str(v) + '||'

        if temp_str.endswith('||'):
            temp_str = temp_str[0:len(temp_str) - 2]
        return temp_str
