import commands
import sys
import os
import inspect

import logging
import logging.config
import ConfigParser
import lib.globalVars as g_vars

logger = logging.getLogger("FroductInfo")


def initConfig():
    conf = ConfigParser.ConfigParser()
    conf.optionxform = str
    conf.read(os.path.normpath("conf/conf.ini"))
    g_vars.workingdir = os.path.normpath(conf.get("base", "workingdir"))
    g_vars.forceLogin = bool(int(conf.get("base", "force_login")))
    g_vars.navie_min_sec = int(conf.get('base', 'navie_min_sec'))
    g_vars.navie_max_sec = int(conf.get('base', 'navie_max_sec'))
    g_vars.webdriver = conf.get('base', 'webdriver')
    g_vars.support_dial = bool(int(conf.get('NetWork', 'support_dial')))
    g_vars.GetUserInfoConf.reconnect_times = int(conf.get('GetUserInfo', 'reconnect_times'))

    g_vars.max_page = int(conf.get('GetSalerInfo', 'max_page'))
    g_vars.next_page_wait_time = int(conf.get('GetSalerInfo', 'next_page_wait_time'))

