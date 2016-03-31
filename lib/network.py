# coding: utf-8

import os
import logging
from common import sleepShowProcess


def ReconnectDial(name=u'本地连接', username=None, passwd=None, wait=5):
    cmd_str = u'rasdial 宽带连接 /disconnect'.encode('gbk')
    os.system(cmd_str)
    sleepShowProcess(wait, u'    断开连接等待 %d 秒... ' % wait)

    cmd_str = u'rasdial 宽带连接 '.encode('gbk')
    ret = os.system(cmd_str)
    if ret == 0:
        sleepShowProcess(wait, u'    连接成功等待 %d 秒... ' % wait)
    else:
        raise SystemError(u'Reconncet Dial Fail .....')
