# coding=utf8

import subprocess
import re
import platform


def find_all_ip(platform):
    ipstr = '([0-9]{1,3}\.){3}[0-9]{1,3}'
    if platform == "Darwin" or platform == "Linux":
        ipconfig_process = subprocess.Popen("ifconfig", stdout=subprocess.PIPE)
        output = ipconfig_process.stdout.read()
        ip_pattern = re.compile('(inet %s)' % ipstr)
        if platform == "Linux":
            ip_pattern = re.compile('(inet addr:%s)' % ipstr)
        pattern = re.compile(ipstr)
        iplist = []
        for ipaddr in re.finditer(ip_pattern, str(output)):
            ip = pattern.search(ipaddr.group())
            iplist.append(ip.group())
        return iplist
    elif platform == "Windows":
        ipconfig_process = subprocess.Popen("ipconfig", stdout=subprocess.PIPE)
        output = ipconfig_process.stdout.read()
        ip_pattern = re.compile("IPv4 Address(\. )*: %s" % ipstr)
        pattern = re.compile(ipstr)
        iplist = []
        for ipaddr in re.finditer(ip_pattern, str(output)):
            ip = pattern.search(ipaddr.group())
            iplist.append(ip.group())
        return iplist


ips = []
try:
    system = platform.system()
    ips = find_all_ip(system)
except Exception as e:
    ips.append('192.168.0.1')


def get_all_ip():
    return ips
