# coding=utf8

import random
import math
import time
import Utils.LogUtils.util.find_all_ip
from threading import RLock
rl = RLock()

class SpanIdGenerator:
    increment_id = 0

    def ip2long(self, ip):
        ret = 0
        ipGroups = []
        ipGroups = ip.split(".")
        ipInt = [0] * 4
        for i in range(len(ipGroups)):
            ipInt[i] = ipGroups[i]

        ret = 0 << 24 | 1 << 16 | 2 << 8 | 3
        return ret

    def timeFactor(self):
        data = long(time.time() * 1000)
        return data

    def timeFactorSecond(self):
        data = long(time.time())
        return data

    def randFactor(self):
        ret = long(random.random() * math.pow(2, 32))
        return ret

    def getLocalIpList(self):

        return find_all_ip.get_all_ip()

    def getIpFactor(self):
        ips = []
        ips = self.getLocalIpList()
        ipAddr = "127.0.0.1"
        if (ips == ""):
            return self.ip2long(ipAddr)
        for iptmp in ips:
            if (iptmp == "127.0.0.1"):
                continue
            else:

                ipAddr = iptmp
                break
        return self.ip2long(ipAddr)

    def create_span_id(self):
        timeFactor = self.timeFactor()
        randFactor = self.randFactor()
        ipFactor = self.getIpFactor()
        spanId = (((ipFactor & timeFactor) & 0xffffffff) << 32) | (randFactor & 0xffffffff)
        return self.handle_sixteen(format(spanId, 'x'))

    def create_trace_id(self):
        timeFactor = self.timeFactorSecond()
        randFactor1 = self.randFactor()

        rl.acquire()
        SpanIdGenerator.increment_id += 1
        rl.release()

        randFactor2 = SpanIdGenerator.increment_id

        traceIdpart1 = self.getIpFactor() << 32 | (timeFactor & 0xffffffff)
        traceIdpart2 = randFactor1 << 32 | (randFactor2 & 0xffffff) << 8 | 0x82

        traceIdpart1 = format(traceIdpart1, 'x')
        traceIdpart2 = format(traceIdpart2, 'x')

        traceIdpart1 = self.handle_sixteen(traceIdpart1)
        traceIdpart2 = self.handle_sixteen(traceIdpart2)
        return traceIdpart1 + traceIdpart2


    def handle_sixteen(self,temp_str):
        if not temp_str :
            return "0000000000000000"
        while (len(temp_str) < 16):
            temp_str = "0" + temp_str
        return temp_str


if __name__ == '__main__':
    sg = SpanIdGenerator()
    tid = sg.create_trace_id()
    tid2 = sg.create_trace_id()
    sid = sg.create_span_id()
    print(tid)
    print(tid2)