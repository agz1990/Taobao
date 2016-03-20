# encoding: utf-8

from __future__ import division
import time
import logging
import random
import sys
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from lib import globalVars as g_vars
from lib.ProgressBar import AnimatedProgressBar

logger = logging.getLogger('FroductInfo')

SEARCH_URL = 'https://s.taobao.com/'
BASE_GOODS_URL = "https://item.taobao.com/item.htm?id="


class UnsaleException(WebDriverException):
    """
    宝贝已经下架
    :param WebDriverException:
    :return:
    """
    pass

class DeleteException(WebDriverException):
    """
    宝贝已经删除
    :param WebDriverException: 
    :return: 
    """
    pass

class GoodInfoUnknowError(WebDriverException):
    """
    宝贝已经删除
    :param WebDriverException:
    :return:
    """
    pass


def sleepShowProcess(sec, msg , width=40):
    custom_options = {
        'end': 100,
        'width': width,
        'fill': '#',
        'format': (msg + u'[%(fill)s%(blank)s] %(progress)s%% ').encode('gbk')
    }
    first = True
    step = float(sec / 100)
    p = AnimatedProgressBar(**custom_options)
    while True:

        if first:
            first = False
        else:
            sys.stdout.write('\b'*(custom_options['width']+4))
        p + 1
        sys.stdout.flush()
        p.show_progress()
        time.sleep(step)
        if p.progress == 100:
            sys.stdout.write('\n')
            break

def HightLightMatchGood(driver, gid, collor = 'red'):

    gid = str(gid)
    items = driver.find_elements_by_class_name('item ')
    matchItems = [i for i in items if i.get_attribute('data-category') == "auctions"]

    goodsItemId = 'J_Itemlist_PLink_%s' % gid
    dealCnt = None
    for i, item in enumerate(matchItems):

        try:
            item.find_element_by_id(goodsItemId)

            # 滚动到指定报宝贝
            item.location_once_scrolled_into_view

            # 高亮商品
            driver.execute_script(
                """var p = document.getElementById('J_Itemlist_PLink_%s');
                p.innerHTML='宝贝 [%s] ';
                p.style.backgroundColor = 'red';""" % (gid, gid))

            matchIndex = i + 1

            totalCnt = driver.find_element_by_id('mainsrp-nav').find_element_by_class_name('total').text

            # 获取多少人购买
            dealCnt = item.find_element_by_class_name('deal-cnt').text

            msg = u"    *** [%s] 匹配到第 %s 个宝贝 【%s】 ***" % (gid, matchIndex, dealCnt)
            logger.debug(msg)
            driver.execute_script("alert('%s')" % msg)

            alert = driver.switch_to.alert
            sleepShowProcess(5, u'    弹出提示框等待 5 秒 ')
            alert.accept()
            return matchIndex, totalCnt, dealCnt
            # goodInfo['defaultDealCnt'] = dealCnt

        except NoSuchElementException, e:
            continue
    #
    # if not dealCnt:
    #     logger.debug(u"    *** [%s] 【综合排序】第一页找不到该宝贝 ***"% gid)

    raise NoSuchElementException(u'宝贝ID [ %s ] 不在本页面 '.encode('gbk') % gid)



        # 本页面没找到报异常


def PageLoadAndRandomWait(driver, url):
    try:
        driver.get(url)

    except TimeoutException:
        logger.info(u'    页面超时， 直接跳过 ...')

    finally:
        navie_min_sec = int(g_vars.navie_min_sec)
        navie_max_sec = int(g_vars.navie_max_sec)
        if navie_max_sec <= navie_min_sec:
            logger.warn(u'    超时时间设置有误 ...')
            sec = 5
        else:
            sec = float(random.choice(range(g_vars.navie_min_sec*1000, g_vars.navie_max_sec*1000)) / 1000)
        sleepShowProcess(sec,  u'    加载网页 随机等待 %0.2f 秒 ' % sec)


def PageLoadFixWait(driver, url, fixsec = 0):
    try:
        driver.get(url)

    except TimeoutException:
        logger.info(u'    页面超时， 直接跳过 ...')

    finally:
        if fixsec != 0:
            sleepShowProcess(fixsec,  u'    加载网页固定等待 %0.2f 秒 ' % fixsec)


def SearchGood(driver, url, gid, maxpage=6):
    # matchIndex, totalCnt, dealCnt
    for i in range(1, maxpage):
        try:
            if i == 1:
                logger.debug(u'    进入搜索页面....')
                if driver.current_url != url:
                    PageLoadFixWait(driver, url, 3)
            else:
                sleepShowProcess(5, u'    等待进入 %s 页查找...' % i)

            matchIndex, totalCnt, dealCnt = HightLightMatchGood(driver, gid)
            return i, matchIndex, totalCnt, dealCnt
            logger.info(u'     找到商品 退出...')
            return

        except NoSuchElementException, e: # 找不到选择下一页
            logger.debug(u"    *** [%s] 第%s页找不到该宝贝 ***" % (gid, i))
            # 本页面找不到点击下一页
            btns = driver.find_element_by_id('mainsrp-pager').find_elements_by_class_name('item')

            try:
                btns[i+1].location_once_scrolled_into_view
                btns[i+1].click()

            except IndexError:
                # 没有下一页了
                raise NoSuchElementException(u'宝贝ID [ %s ] 在前%s页找不到 '.encode('gbk') % (gid, i))







def WaitForLogind(driver):
    logger.info(u"*** 登录淘宝首页 ***")
    driver.get("https://www.taobao.com/")

    while True:
        try:
            driver.find_element_by_class_name('login-info-nick')
            logger.info(u"登录成功...")
            time.sleep(3)
            break

        except NoSuchElementException, e:
            print(u"你还没登录淘宝，请登录 .....")
            time.sleep(5)


def getGoodsTitle(driver, gid):
    tmailGoodFlag = False
    status = u'在售'
    title = ''
    url = BASE_GOODS_URL + str(gid)
    logger.debug(u"    跳转到 宝贝页面 【%s】...." % url)

    PageLoadAndRandomWait(driver, url)
    current_url = driver.current_url
    if url != current_url:
        tmailGoodFlag = True

    try:
        if tmailGoodFlag:  # 天猫宝贝
            elememts = driver.find_elements_by_tag_name('h1')
            for e in elememts:
                if e.get_attribute('data-spm'):
                    title = e.text

            if not title:
                raise NoSuchElementException('天猫宝贝[ %s ]找不到标题 ....' % gid)

            logger.debug(u"    获取到【天猫】宝贝标题为 【%s】...." % title)
        else: # 淘宝宝贝标题
            title = driver.find_element_by_class_name('tb-main-title').get_attribute("data-title")
            logger.debug(u"    获取到【淘宝】宝贝标题为 【%s】...." % title)

        try: # 判断商品是否在售
            driver.find_element_by_class_name('J_LinkBuy')
        except NoSuchElementException:
            try:
                driver.find_element_by_id ('J_LinkBuy')
            except NoSuchElementException:
                status = u'下架'

    except NoSuchElementException:
        # TODO 判断商品是否已经删除

        if current_url.find('.taobao.com/market') == -1 and current_url.find('auction/noitem.htm') == -1:
            # raise GoodInfoUnknowError(u'获取标题未知异常...')
            status = u'未知'
            pass
        else:
            status = u'删除'

    return title, tmailGoodFlag, status


def processOneGoods(driver, gid):

    gid = str(gid)
    goodInfo = {
        'id': gid,
        'from': u'淘宝',
        'status' : u'在售',
        'titie': '',
        'defaultDealCnt': u'找不到',
        'defaultTotal': '',
        'saleOrderDealCnt': u'找不到',
        'saleOrderTotal': '',
    }

    (goodInfo['titie'], _, status) = getGoodsTitle(driver, gid)

    if _:
        goodInfo['from'] = u'天猫'

    if goodInfo['status'] != status: # 商品已经删除了或者下架
        logger.info(u'    *** 商品已经 【%s】 了不用再查找.' % status)
        goodInfo['status'] = status
        return goodInfo


    logger.debug(u"    跳转到 搜索页面: %s" % SEARCH_URL)
    PageLoadAndRandomWait(driver, SEARCH_URL)
    inputElement = driver.find_element_by_id('q')
    inputElement.send_keys(goodInfo['titie'])
    btn = driver.find_element_by_class_name('btn-search')
    logger.debug(u"    等待页面跳转 ...")
    time.sleep(1)

    try:
        btn.submit()
    except TimeoutException:
        pass

    # return
    logger.debug(u"    页面加载成功完成， 搜索宝贝 ...")

    # 获取所有宝贝信息
    goodInfo['defaultTotal'] = u'找到' + driver.find_element_by_id('mainsrp-nav').find_element_by_class_name('total').text
    logger.debug(u"    默认排序页面加载成功 【%s】 开始搜索宝贝 ..." % goodInfo['defaultTotal'])
    items = driver.find_elements_by_class_name('item ')
    matchItems = [i for i in items if i.get_attribute('data-category') == "auctions"]

    goodsItemId = 'J_Itemlist_PLink_%s' % gid
    dealCnt = None
    for i, item in enumerate(matchItems):

        try:
            item.find_element_by_id(goodsItemId)
            # 获取多少人购买
            dealCnt = item.find_element_by_class_name('deal-cnt').text
            goodInfo['defaultDealCnt'] = dealCnt
            matchIndex = i + 1

        except NoSuchElementException, e:
            continue

    if dealCnt:
        logger.debug(u"    *** [%s] 匹配到第 %s 个宝贝 【%s】 ***" % (gid, matchIndex, dealCnt))
    else:
        logger.debug(u"    *** [%s] 【综合排序】第一页找不到该宝贝 ***"% gid)


    dealCnt = None

    # nextUrl= re.sub('default$', 'sale-desc', driver.current_url)
    nextUrl = driver.current_url + '&sort=sale-desc'
    logger.debug(u"    跳转到按销量排序页面  ...")
    PageLoadAndRandomWait(driver, nextUrl)

    # # 获取所有宝贝信息
    # goodInfo['saleOrderTotal'] = u'销量找到' + driver.find_element_by_id('mainsrp-nav').find_element_by_class_name('total').text
    # logger.debug(u"    按销量排序页面加载成功 【%s】 开始搜索宝贝 ..." % goodInfo['saleOrderTotal'])

    items = driver.find_elements_by_class_name('item ')
    matchItems = [i for i in items if i.get_attribute('data-category') == "auctions"]

    goodsItemId = 'J_Itemlist_PLink_%s' % gid
    for i, item in enumerate(matchItems):

        try:
            item.find_element_by_id(goodsItemId)
            # 获取多少人购买
            dealCnt = item.find_element_by_class_name('deal-cnt').text
            matchIndex = i + 1
            goodInfo['saleOrderDealCnt'] = dealCnt

        except NoSuchElementException, e:
            continue

    if dealCnt:
        logger.debug(u"    *** [%s] 匹配到第 %s 个宝贝 【%s】 ***" % (gid, matchIndex, dealCnt))
    else:
        logger.debug(u"    *** [%s] 【销量排序】第一页找不到该宝贝 ***" % gid)

    return goodInfo
