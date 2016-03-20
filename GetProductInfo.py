# coding: utf-8
import time
import sys
import re
import os
import traceback
import logging
import logging.config
from glob import glob
from pprint import pprint
import random
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
# from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
# from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0

from lib.conf import initConfig
from lib import globalVars as g_vars
from lib.globalVars import driver
from lib import taobao
from lib.taobao import sleepShowProcess

logging.config.fileConfig('log.conf')
logger = logging.getLogger('FroductInfo')

SEARCH_URL = 'https://s.taobao.com/'
BASE_GOODS_URL = "https://item.taobao.com/item.htm?id="


#
# 启动文件： GetProductInfo.exe
# 配置文件: conf/conf.ini
#
# 1. 启动程序， 准备好 宝贝ID写入到 *.list(所有以*.list结尾的文件名都行) 结尾的文件，保存。
# 2. 把写好点 *.list 拷贝到 workingdir 目录下，程序会主动去扫描该目录下 *.list结尾的文件读入程序进行查找
# 3. 程序运行完成，得到 *.result 结尾的文件，就是结果
# 4. 程序会将正在处理的文件后缀名修改为 .proc
# 5. 最终将生成结果文件 *.result

def ProcessOneFile(driver, f, rename=False):
    currentFilenName = f
    processFileName = currentFilenName[:-5] + '.proc'
    finishFileName = currentFilenName[:-5] + '.finish'
    resultFileName = currentFilenName[:-5] + '.result'
    logger.info(u'*** 开始处理文件: %s ***' % currentFilenName)

    if rename:
        os.rename(currentFilenName, processFileName)
    else:
        processFileName = currentFilenName

    if os.path.exists(resultFileName):
        os.remove(resultFileName)

    successCnt = 0
    errorCnt = 0

    with open(processFileName) as fhandle:
        # idlist = [line.strip() for line in fhandle if len(line.strip()) > 5 and re.match('\d+', line)]

        idlist = []
        for index, line in enumerate(fhandle):
            line = line.strip()
            if re.match(r'^\d+$', line):
                idlist.append(line)
            else:
                # logger.warn(u'无效行 %5d : %s' % (index+1, line.decode('utf-8')) )
                pass


        logger.info(u'本文件有 %d 个有效 id. ' % len(idlist))
        for index, gid in enumerate(idlist):
            resultStr = ''
            try:
                logger.info(u'*** 开始处理第 %4d 个 [ %s ]  ***' % (index + 1, gid))
                # g = taobao.processOneGoods(driver, gid)
                goods = taobao.Goods(driver, gid, index + 1)
                goods.Process()
                # resultStr = u"%03d|%12s|%s|%s|%14s|%8s|%8s|" % (
                #     index + 1, g['id'],  g['from'], g['status'], g['defaultTotal'], g['defaultDealCnt'],
                #      g['saleOrderDealCnt']
                # )
                resultStr = goods.getToFileStr()

                successCnt += 1
                time.sleep(1)
                logger.info(u'*** 第 %4d 个 [ %s ] 处理成功 ***' % (index + 1, gid))
            except Exception, e:

                errorCnt += 1
                # resultStr = u"%03d|%12s|%s" % (
                #     index + 1, gid, u'异常'
                # )
                resultStr = u"# NO. {seq:04d} |{id:^14s}| 异常".format(seq=index+1, id=gid)
                logger.error(u'*** 第 %4d 个 [ %s ] 处理失败 ***' % (index + 1, gid))
                logger.error(traceback.format_exc())

            finally:
                logger.info(resultStr)
                with open(resultFileName, 'a') as retFile:
                    resultStr += '\n'
                    retFile.write(resultStr.encode('utf-8'))

    logger.info(u'*** 文件 %s 处理完毕 成功 %d 失败 %d ***' % (currentFilenName, successCnt, errorCnt))
    if rename:
        os.rename(processFileName, finishFileName)
    # if g_vars.debug:
    #     logger.debug('调试模式将 ' % )
    #     os.rename(processFileName, currentFilenName)


def MainLoop():

    init()

    driver = g_vars.driver
    if g_vars.forceLogin:
        taobao.WaitForLogind(g_vars.driver)

    cnt = 0
    while True:
        flist = glob('*.list')
        processingFiles = glob('*.proc')
        processingFiles.extend(flist)
        logger.info(u'扫描目录 %s 获取待处理文件(%s)个 第 %d 次扫描' % (g_vars.workingdir, len(processingFiles), cnt))

        try:
            ProcessOneFile(driver, processingFiles.pop())
        except IndexError:
            cnt += 1
            sleepShowProcess(30, u'没有需要处理的文件 等待 30 秒 ')



    driver.quit()
    time.sleep(3)

def init():

    initConfig()
    logger.info(u"########################################")
    logger.info(u"# 网页超时时间: %d 秒" % g_vars.load_page_time_out)
    logger.info(u"# 等待时间: %d ~ %d 秒" % (g_vars.navie_min_sec, g_vars.navie_max_sec))
    logger.info(u"# 强制用户登录: %s " % g_vars.forceLogin)
    logger.info(u"# 浏览器的类型: %s " % g_vars.webdriver)
    logger.info(u"########################################\n")


    logger.info(u"*** 打开浏览器 ***")


    if g_vars.webdriver == 'chrome':
        g_vars.driver = webdriver.Chrome()
    else:
        g_vars.driver = webdriver.Firefox()

    g_vars.driver.set_page_load_timeout(int(g_vars.load_page_time_out))
    g_vars.driver.set_script_timeout(int(g_vars.load_page_time_out))

    os.chdir(g_vars.workingdir)


def test():

    if driver == None:
        init()
    with open('list.full') as f: idlist = [line.strip() for line in f if len(line.strip()) > 5]

"""
logger.info(u"*** 打开浏览器 ***")
driver = webdriver.Firefox()
driver.set_page_load_timeout(int(g_vars.load_page_time_out))
driver.set_script_timeout(int(g_vars.load_page_time_out))
"""

if __name__ == '__main__':
    MainLoop()
