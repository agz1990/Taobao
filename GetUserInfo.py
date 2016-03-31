# coding: utf-8
import time
import sys
import re
import os
import traceback
import logging
import logging.config
from glob import glob
import random
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from lib.conf import initConfig
from lib import globalVars as g_vars
from lib.globalVars import driver
from lib import taobao
from lib.network import ReconnectDial
from lib.taobao import sleepShowProcess, PageLoadAndRandomWait

logging.config.fileConfig('log.conf')
logger = logging.getLogger('FroductInfo')

SEARCH_URL = 'http://www.taoyitu.com/'
BLOCK_URL = 'http://www.taoyitu.com/Shield.html'


#
# 启动文件： GetProductInfo.exe
# 配置文件: conf/conf.ini
#
# 1. 启动程序， 准备好 宝贝ID写入到 *.list(所有以*.list结尾的文件名都行) 结尾的文件，保存。
# 2. 把写好点 *.list 拷贝到 workingdir 目录下，程序会主动去扫描该目录下 *.list结尾的文件读入程序进行查找
# 3. 程序运行完成，得到 *.result 结尾的文件，就是结果
# 4. 程序会将正在处理的文件后缀名修改为 .proc
# 5. 最终将生成结果文件 *.result

def ProcessOneUID(driver, uid, seq=1):
    if g_vars.support_dial and g_vars.GetUserInfoConf.reconnect_times:
        if g_vars.process_times > 0 and g_vars.process_times % g_vars.GetUserInfoConf.reconnect_times == 0:
            logger.info(u'     重新拨号....')
            ReconnectDial()
    result = u''
    try:
        uid = uid.decode('gbk')
    except UnicodeDecodeError:
        pass
    except UnicodeEncodeError:
        pass

    PageLoadAndRandomWait(driver, SEARCH_URL)
    try:
        inputElement = driver.find_element_by_id('txt_name')
        inputElement.clear()
        inputElement.send_keys(uid)
        searchElement = driver.find_element_by_id('search_btn')
        searchElement.click()
        sleepShowProcess(5, u'    提交用户ID        等待 5 秒 ')

        try:
            # WebDriverWait(driver, 20).until(lambda dr: dr.find_element_by_id('rate_userName').is_displayed())

            WebDriverWait(driver, 20).until(lambda dr: dr.find_element_by_id('rate_userName').text == uid)
            if uid == driver.find_element_by_id('rate_userName').text:
                userTime = driver.find_element_by_id('rate_userTime').text
                buyerCount = driver.find_element_by_id('spanUserBuyerCount').text
                userIdent = driver.find_element_by_id('rate_userIdent').text
                ipAddress = driver.find_element_by_id('buyer_IpAddress').text
                result = u"""# NO. {:04d} | {:20s}| {:20s}| {:20s}| {:20s}| {}""" \
                    .format(seq, uid, userIdent, userTime, buyerCount, ipAddress)

        except TimeoutException ,e:

            errElemnet = driver.find_element_by_id('UserInfo')
            if errElemnet.is_displayed():  # 账号不存在
                errHint = errElemnet.text
                if u'该号不存在' in errHint:
                    result = u"""# NO. {:04d} | {:20s}| {}""".format(seq, uid, errHint)
                elif u'查询速度过快' in errHint:
                    sleepShowProcess(60, u'    查询速度过快        等待 60 秒 ')
                    result = ProcessOneUID(driver, uid, seq)
                else:  # 其他错误提示
                  result = u"""# NO. {:04d} | {:20s}| {}""".format(seq, uid, errHint)
            else:
                raise NoSuchElementException(u'ProcessOneUID Know Error: url:%s' % driver.current_url)

    except NoSuchElementException, e:
        if driver.current_url == BLOCK_URL:
            logger.info(u'     当前IP被屏蔽重新拨号....')
            if g_vars.support_dial:
                ReconnectDial()
            return ProcessOneUID(driver, uid, seq)
        else:
            raise e

    g_vars.process_times += 1
    return result

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
            if len(line.strip()) > 0:
                try:
                    line = line.decode('gbk')
                except UnicodeDecodeError:
                    pass
                idlist.append(line.strip())

        logger.info(u'本文件有 %d 个有效 id. ' % len(idlist))
        for index, uid in enumerate(idlist):

            resultStr = ''
            try:
                logger.info(u'*** 开始处理第 %4d 个 [ %s ]  ***' % (index + 1, uid))

                resultStr = ProcessOneUID(driver, uid, index + 1)

                successCnt += 1
                time.sleep(1)
                logger.info(u'*** 第 %4d 个 [ %s ] 处理成功 ***' % (index + 1, uid))

            except Exception, e:

                errorCnt += 1
                resultStr = u"""# NO. {:04d} |{:20s}| {:20s}""".format(index + 1, uid, u'异常')
                logger.error(u'*** 第 %4d 个 [ %s ] 处理失败 ***' % (index + 1, uid))
                logger.error(traceback.format_exc())

            finally:
                logger.info(resultStr)
                with open(resultFileName, 'a') as retFile:
                    resultStr += '\n'
                    retFile.write(resultStr.encode('utf-8'))

    logger.info(u'*** 文件 %s 处理完毕 成功 %d 失败 %d ***' % (currentFilenName, successCnt, errorCnt))
    if rename:
        os.rename(processFileName, finishFileName)


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
            ProcessOneFile(driver, processingFiles.pop(), True)
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
    logger.info(u"# 支持重新拨号: %s " % g_vars.support_dial)
    logger.info(u"# 多少次进行重连: %s " % g_vars.GetUserInfoConf.reconnect_times)
    logger.info(u"# 浏览器的类型: %s " % g_vars.webdriver)
    logger.info(u"########################################\n")

    logger.info(u"*** 打开浏览器 ***")

    if g_vars.webdriver == 'chrome':
        g_vars.driver = webdriver.Chrome()
    else:
        g_vars.driver = webdriver.Firefox()

    g_vars.driver.get(SEARCH_URL)
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
