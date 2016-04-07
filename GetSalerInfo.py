# coding: utf-8
import time
import sys
import re
import os
import traceback
import logging
import urllib2
import json
import chardet
import logging.config
from glob import glob
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



#
# 启动文件： GetUserInfo.exe
# 配置文件: conf/conf.ini
#
# 1. 启动程序， 准备好 宝贝ID写入到 *.list(所有以*.list结尾的文件名都行) 结尾的文件，保存。
# 2. 把写好点 *.list 拷贝到 workingdir 目录下，程序会主动去扫描该目录下 *.list结尾的文件读入程序进行查找
# 3. 程序运行完成，得到 *.result 结尾的文件，就是结果
# 4. 程序会将正在处理的文件后缀名修改为 .proc
# 5. 最终将生成结果文件 *.result

def ProcessOneLine(driver, line, seq=1, fname='xxx.result'):
    max_page = g_vars.max_page
    g_vars.debugInfo = []
    for index in range(max_page):
        page = index + 1
        if page == 1:
            PageLoadAndRandomWait(driver, line)

        shops = driver.find_elements_by_class_name('shopname')
        for index, shop in enumerate(shops):

            shopId = shop.get_attribute('data-userid')
            wangwangName = shop.find_elements_by_tag_name('span')[-1].text
            logStr = u'# %03d | P%03d@%02d | %10s |' % (seq, page, index, shopId)
            shopId = shop.get_attribute('data-userid')
            level = u'未知'
            try:
                url = 'https://s.taobao.com/api?sid=%s&callback=shopcard&app=api&m=get_shop_card' % shopId
                f = urllib2.urlopen(url)
                returnLines = f.readlines()
                jsondata = returnLines[2][9:-2]
                matchinof = re.search(r'"icon-supple-level-([^"]*?)"', returnLines[2][9:-2])
                if matchinof:
                    level = matchinof.groups()[0]

                if level == 'xin':
                    level = u'红心'
                elif level == 'zuan':
                    level = u'钻石'
                elif level == 'guan':
                    level = u'蓝冠'
                elif level == 'jinguan':
                    level = u'金冠'


                ret = json.loads(jsondata)

                levelCnt = len(ret['levelClasses'])
                # isTmall = u'是' if ret['isTmall'] else u'否'
                # isQiye = u'是' if ret['isQiye'] else u'否'

                if ret['isTmall']:
                    shopType = u'天猫'
                elif ret['isQiye']:
                    shopType = u'企业'
                else:
                    shopType = u'淘宝'

                logStr += shopType + u"|%s%s| " % (level, levelCnt) + wangwangName

                levelName = level+str(levelCnt)
                finalFileName = shopType + '_' + levelName + '_' + fname
                with open(finalFileName, 'a') as retFile:
                    retFile.write(logStr.encode('utf-8')+'\n')

            except Exception, e:

                logStr += u' 获取信誉异常(%s) | ' % e  + wangwangName


            # logStr = u'NO. %04s 第 %03s 页 %02s 个 ID:%11s 天猫: %s 企业: %s [%s %d] %s ' \
            #          % (seq, page, index, shopId, isTmall, isQiye, level, levelCnt, wangwangName)

            with open(fname, 'a') as retFile:
                retFile.write(logStr.encode('utf-8')+'\n')


            with open('ID+NAME_' + fname, 'a') as retFile:
                line = shopId + '\t' + wangwangName
                retFile.write(line.encode('utf-8')+'\n')

            g_vars.debugInfo.append(ret)
            logger.debug(logStr.strip())
        if page != max_page:
            driver.find_element_by_partial_link_text(u'下一页').click()
            sleepShowProcess(g_vars.next_page_wait_time, u'     翻页等待 %s 秒 ' % g_vars.next_page_wait_time)


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

    # if os.path.exists(resultFileName):
    #     os.remove(resultFileName)

    successCnt = 0
    errorCnt = 0

    with open(processFileName) as fhandle:
        # lines = [line.strip() for line in fhandle if len(line.strip()) > 5 and re.match('\d+', line)]

        lines = []
        for index, line in enumerate(fhandle):
            if len(line.strip()) > 0:
                try:
                    line = line.decode('GB2312')
                except UnicodeDecodeError:
                    try:
                        line = line.decode('utf-8')
                    except UnicodeEncodeError:
                        pass
                lines.append(line.strip())

        logger.info(u'本文件有 %d 个有效 id. ' % len(lines))
        for index, line in enumerate(lines):

            resultStr = ''
            try:
                logger.info(u'*** 开始处理第 %4d 个 [ %s ]  ***' % (index + 1, line))

                ProcessOneLine(driver, line, index + 1, resultFileName)

                successCnt += 1
                time.sleep(1)
                logger.info(u'*** 第 %4d 个 [ %s ] 处理成功 ***' % (index + 1, line))

            except Exception, e:

                errorCnt += 1
                logger.error(u'*** 第 %4d 个 [ %s ] 处理失败 ***' % (index + 1, line))
                logger.error(traceback.format_exc())

            finally:
                pass

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
    logger.info(u"# 下一页等待时间: %d 秒" % g_vars.next_page_wait_time)
    logger.info(u"# 最大页面数: %d 秒" % g_vars.max_page)
    logger.info(u"# 浏览器的类型: %s " % g_vars.webdriver)
    logger.info(u"########################################\n")

    logger.info(u"*** 打开浏览器 ***")
    if g_vars.webdriver == 'chrome':
        g_vars.driver = webdriver.Chrome()
    else:
        g_vars.driver = webdriver.Firefox()

    g_vars.driver.get('https://www.taobao.com/')
    g_vars.driver.set_page_load_timeout(int(g_vars.load_page_time_out))
    g_vars.driver.set_script_timeout(int(g_vars.load_page_time_out))

    os.chdir(g_vars.workingdir)


"""
logger.info(u"*** 打开浏览器 ***")
driver = webdriver.Firefox()
driver.set_page_load_timeout(int(g_vars.load_page_time_out))
driver.set_script_timeout(int(g_vars.load_page_time_out))
"""

if __name__ == '__main__':
    MainLoop()
