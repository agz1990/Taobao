# encoding: utf-8

import time
import logging
import random
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from lib import globalVars as g_vars

logger = logging.getLogger('FroductInfo')

SEARCH_URL = 'https://s.taobao.com/'
BASE_GOODS_URL = "https://item.taobao.com/item.htm?id="


def PageLoadAndRandomWait(driver, url):
    try:
        driver.get(url)
        navie_min_sec = int(g_vars.navie_min_sec)
        navie_max_sec = int(g_vars.navie_max_sec)
        if navie_max_sec <= navie_min_sec:
            logger.warn(u'    超时时间设置有误 ...')
            sec = 5
        else:
            sec = random.choice(range(g_vars.navie_min_sec, g_vars.navie_max_sec))
        logger.debug(u'    加载网页 随机等待 %0.2f 秒' % sec)
        time.sleep(sec)
    except TimeoutException:
        logger.info(u'    页面超时， 直接跳过 ...')


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
    title = ''
    url = BASE_GOODS_URL + str(gid)
    logger.debug(u"    跳转到 商品页面 【%s】...." % url)

    PageLoadAndRandomWait(driver, url)
    if url != driver.current_url:
        tmailGoodFlag = True
    if tmailGoodFlag:  # 天猫商品
        elememts = driver.find_elements_by_tag_name('h1')
        for e in elememts:
            if e.get_attribute('data-spm'):
                title = e.text

        if not title:
            raise NoSuchElementException('天猫商品[ %s ]找不到标题 ....' % gid)

        logger.debug(u"    获取到【天猫】商品标题为 【%s】...." % title)
    else: # 淘宝商品标题
        title = driver.find_element_by_class_name('tb-main-title').get_attribute("data-title")
        logger.debug(u"    获取到【淘宝】商品标题为 【%s】...." % title)


    return title, tmailGoodFlag


def processOneGoods(driver, gid):
    goodInfo = {
        'id': gid,
        'from': u'淘宝',
        'titie': '',
        'defaultDealCnt': u'找不到',
        'defaultTotal': '',
        'saleOrderDealCnt': u'找不到',
        'saleOrderTotal': '',
    }

    (goodInfo['titie'], _) = getGoodsTitle(driver, gid)

    if _:
        goodInfo['from'] = u'天猫'

    logger.debug(u"    跳转到 搜索页面: %s...." % SEARCH_URL)
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
    logger.debug(u"    页面加载成功完成， 搜索商品 ...")

    # 获取所有商品信息
    goodInfo['defaultTotal'] = u'默认找到' + driver.find_element_by_id('mainsrp-nav').find_element_by_class_name('total').text
    logger.debug(u"    默认排序页面加载成功 【%s】 开始搜索商品 ..." % goodInfo['defaultTotal'])
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
        logger.debug(u"    *** [%s] 匹配到第 %s 个商品 【%s】 ***" % (gid, matchIndex, dealCnt))
    else:
        logger.debug(u"    *** [%s] 【综合排序】第一页找不到该商品...")

    # nextUrl= re.sub('default$', 'sale-desc', driver.current_url)
    nextUrl = driver.current_url + '&sort=sale-desc'
    logger.debug(u"    跳转到按销量排序页面  ...")
    PageLoadAndRandomWait(driver, nextUrl)

    # 获取所有商品信息
    goodInfo['saleOrderTotal'] = u'销量找到' + driver.find_element_by_id('mainsrp-nav').find_element_by_class_name('total').text
    logger.debug(u"    按销量排序页面加载成功 【%s】 开始搜索商品 ..." % goodInfo['saleOrderTotal'])

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
        logger.debug(u"    *** [%s] 匹配到第 %s 个商品 【%s】 ***" % (gid, matchIndex, dealCnt))
    else:
        logger.debug(u"    *** [%s] 【销量排序】第一页找不到该商品...")

    return goodInfo
