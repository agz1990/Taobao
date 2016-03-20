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


class GoodInfosUnknowError(WebDriverException):
    """
    宝贝已经删除
    :param WebDriverException:
    :return:
    """
    pass


def sleepShowProcess(sec, msg, width=40):
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
            sys.stdout.write('\b' * (custom_options['width'] + 4))
        p + 1
        sys.stdout.flush()
        p.show_progress()
        time.sleep(step)
        if p.progress == 100:
            sys.stdout.write('\n')
            break


def HightLightMatchGood(driver, gid, collor='red'):
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
            sleepShowProcess(5, u'    弹出提示框等待 5 秒      ')
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
            sec = float(random.choice(range(g_vars.navie_min_sec * 1000, g_vars.navie_max_sec * 1000)) / 1000)
        sleepShowProcess(sec, u'    加载网页 随机等待 %0.2f 秒 ' % sec)


def PageLoadFixWait(driver, url, fixsec=0):
    try:
        driver.get(url)

    except TimeoutException:
        logger.info(u'    页面超时， 直接跳过 ...')

    finally:
        if fixsec != 0:
            sleepShowProcess(fixsec, u'    加载网页固定等待 %0.2f 秒 ' % fixsec)


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


def SearchGoods(driver, url, gid, maxpage=6):
    # matchIndex, totalCnt, dealCnt
    for i in range(1, maxpage):
        try:
            if i == 1:
                logger.debug(u'    进入搜索页面....')
                if driver.current_url != url:
                    PageLoadFixWait(driver, url, 3)
            else:
                sleepShowProcess(5, u'    等待进入 %s 页查找...     ' % i)

            matchIndex, totalCnt, dealCnt = HightLightMatchGood(driver, gid)
            logger.info(u'    第 %s 页第 %s 个找到宝贝 [ %s ]...' % (i, matchIndex, gid))
            return i, matchIndex, totalCnt, dealCnt

        except NoSuchElementException, e:  # 找不到选择下一页
            # logger.debug(u"    *** [%s] 第%s页找不到该宝贝 ***" % (gid, i))
            # 本页面找不到点击下一页
            btns = driver.find_element_by_id('mainsrp-pager').find_elements_by_class_name('item')

            try:
                btns[i + 1].location_once_scrolled_into_view
                btns[i + 1].click()

            except IndexError:
                # 没有下一页了
                raise NoSuchElementException(u'宝贝ID [ %s ] 在前%s页找不到 '.encode('gbk') % (gid, i))


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
        else:  # 淘宝宝贝标题
            title = driver.find_element_by_class_name('tb-main-title').get_attribute("data-title")
            logger.debug(u"    获取到【淘宝】宝贝标题为 【%s】...." % title)

        try:  # 判断商品是否在售
            driver.find_element_by_class_name('J_LinkBuy')
        except NoSuchElementException:
            try:
                driver.find_element_by_id('J_LinkBuy')
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
        'status': u'在售',
        'title': '',
        'defaultDealCnt': u'找不到',
        'defaultTotal': '',
        'saleOrderDealCnt': u'找不到',
        'saleOrderTotal': '',
    }

    (goodInfo['title'], _, status) = getGoodsTitle(driver, gid)

    if _:
        goodInfo['from'] = u'天猫'

    if goodInfo['status'] != status:  # 商品已经删除了或者下架
        logger.info(u'    *** 商品已经 【%s】 了不用再查找.' % status)
        goodInfo['status'] = status
        return goodInfo

    logger.debug(u"    跳转到 搜索页面: %s" % SEARCH_URL)
    PageLoadAndRandomWait(driver, SEARCH_URL)
    inputElement = driver.find_element_by_id('q')
    inputElement.send_keys(goodInfo['title'])
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
        logger.debug(u"    *** [%s] 【综合排序】第一页找不到该宝贝 ***" % gid)

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


def processOneGoods2(driver, gid):
    gid = str(gid)
    goodsInfo = {
        'id': gid,
        'from': u'淘宝',
        'status': u'在售',
        'title': '',
        'defaultDealCnt': u'找不到',
        'defaultTotal': '',
        'saleOrderDealCnt': u'找不到',
        'saleOrderTotal': '',
    }

    (goodsInfo['title'], _, status) = getGoodsTitle(driver, gid)

    if _:
        goodsInfo['from'] = u'天猫'

    if goodsInfo['status'] != status:  # 商品已经删除了或者下架
        logger.info(u'    *** 商品已经 【%s】 了不用再查找.' % status)
        goodsInfo['status'] = status
        return goodsInfo

    logger.debug(u"    跳转到 搜索页面: %s" % SEARCH_URL)
    PageLoadAndRandomWait(driver, SEARCH_URL)
    inputElement = driver.find_element_by_id('q')
    inputElement.send_keys(goodsInfo['title'])
    btn = driver.find_element_by_class_name('btn-search')
    logger.debug(u"    等待页面跳转 ...")
    time.sleep(1)

    try:
        btn.submit()
    except TimeoutException:
        pass

    # 默认页面搜索
    defaultUrl = driver.current_url
    (page, matchIndex, totalCnt, dealCnt) = SearchGoods(driver, defaultUrl, gid)

    nextUrl = defaultUrl + '&sort=sale-desc'
    (page, matchIndex, totalCnt, dealCnt) = SearchGoods(driver, nextUrl, gid)

    return goodsInfo


class SearchResult(object):
    def __init__(self):
        pass


class GoodsSearchResult(SearchResult):
    def __init__(self, result={}):
        for k, v in result.items():
            setattr(self, k, v)

    def __str__(self):
        if hasattr(self, 'page') and hasattr(self, 'index'):
            return u'P%d@%02d#%11s' % (self.page, self.index, self.dealCnt)
        else:
            return u'*** Notfound ***'

    def __unicode__(self):
        if hasattr(self, 'page') and hasattr(self, 'index'):
            return u'第 %02d 页 第 %02d 找到 %s 用时 %0.2f 秒' % (self.page, self.index, self.dealCnt, self.timeit)
        else:
            return u'*** 找不到 ***'

    def simpleResult(self):
        if hasattr(self, 'page') and hasattr(self, 'index'):
            return u'P%d@%02d#%11s' % (self.page, self.index, self.dealCnt)
        else:
            return u'*** Notfound ***'


class SearchUtils(object):
    @staticmethod
    def SearchGoods(driver, g, searchUrl=None, maxPage=0, nextPageWaitSec=0):

        # if not isinstance(g, Goods):
        #     raise TypeError(u'Not a Goods')

        if searchUrl == None:
            searchUrl = driver.current_url

        if maxPage <= 0:
            maxPage = g_vars.search_maxpage

        if nextPageWaitSec <= 0:
            nextPageWaitSec = g_vars.search_next_page_wait_sec

        gid = g.gid

        beginTime = time.time()

        for i in range(1, maxPage+1):
            try:
                if i == 1:
                    logger.debug(u'    开始进入 1 页查找...')
                    if driver.current_url != searchUrl:
                        PageLoadFixWait(driver, searchUrl, nextPageWaitSec)
                else:
                    sleepShowProcess(nextPageWaitSec, u'    等待进入 %s 页查找...     ' % i)

                matchIndex, totalCnt, dealCnt = HightLightMatchGood(driver, gid)
                logger.info(u'    第 %s 页第 %s 个找到宝贝 [ %s ]...' % (i, matchIndex, gid))
                result = {
                    'searchUrl': searchUrl,
                    'page': i,
                    'index': matchIndex,
                    'totalCnt': totalCnt,
                    'dealCnt': dealCnt,
                    'timeit': time.time() - beginTime,
                }

                return GoodsSearchResult(result)

            except NoSuchElementException, e:  # 找不到选择下一页
                # logger.debug(u"    *** [%s] 第%s页找不到该宝贝 ***" % (gid, i))
                # 本页面找不到点击下一页
                btns = driver.find_element_by_id('mainsrp-pager').find_elements_by_class_name('item')

                try:
                    btns[i + 1].location_once_scrolled_into_view
                    btns[i + 1].click()

                except IndexError:
                    # 没有下一页了
                    break
                    # raise NoSuchElementException(u'宝贝ID [ %s ] 在前%s页找不到 '.encode('gbk') % (gid, i))

        result = {
            'searchUrl': searchUrl,
            'timeit': time.time() - beginTime,
        }
        return GoodsSearchResult(result)

class Goods(object):
    BASE_DETAIL_URL_PERFIX = "https://item.taobao.com/item.htm?id="

    # 在哪个商称
    FROM_TMAIL = u'天猫'
    FROM_TAOBAO = u'淘宝'

    # 宝贝状态
    STATUS_SALING = u'在售'
    STATUS_UNSALE = u'下架'
    STATUS_DELETE = u'删除'
    STATUS_UNKNOWN = u'未知'

    def __init__(self, driver, gid, seq=1):
        self.seq = seq
        self.gid = str(gid)
        self.title = None
        self.where = Goods.FROM_TAOBAO
        self.driver = driver
        self.status = Goods.STATUS_UNKNOWN
        self.totalCnt = 0
        self.itemInfoUrl = Goods.BASE_DETAIL_URL_PERFIX + self.gid
        self.baseSearchUrl = None
        self.baseSearResult = GoodsSearchResult()
        self.saleSearchUrl = None
        self.saleSearchResult = GoodsSearchResult()

    # 处理一个商品
    def Process(self):
        driver = self.driver

        # 获取宝贝详情
        self.getDetailInfo()

        if self.status != Goods.STATUS_SALING:
            logger.info(u"%s" % unicode(self))
            return

        # 跳转到搜索宝贝页面
        self.naiveToSearch()

        # 获取宝贝默认搜索页面并保存
        self.baseSearchUrl = driver.current_url

        # 在默认页面搜索宝贝
        logger.info(u'    按综合查找 ...')
        self.baseSearResult = SearchUtils.SearchGoods(self.driver, self, self.baseSearchUrl)

        if hasattr(self.baseSearResult, 'totalCnt'):
            self.totalCnt = self.baseSearResult.totalCnt

        # # 获取销量信息
        logger.info(u'    按销量查找 ...')
        self.saleSearchUrl = self.baseSearchUrl + '&sort=sale-desc'
        self.saleSearchResult = SearchUtils.SearchGoods(self.driver, self, self.saleSearchUrl)

        logger.info(u"%s" % unicode(self))

    def getDetailInfo(self):

        driver = self.driver
        gid = self.gid

        tmailGoodFlag = False
        logger.debug(u"    跳转到 宝贝页面 【%s】...." % self.itemInfoUrl)

        PageLoadAndRandomWait(driver, self.itemInfoUrl)
        current_url = driver.current_url
        if self.itemInfoUrl != current_url:
            tmailGoodFlag = True
            self.where = Goods.FROM_TMAIL
            self.itemInfoUrl = current_url

        try:
            if tmailGoodFlag:  # 天猫宝贝
                elememts = driver.find_elements_by_tag_name('h1')
                for e in elememts:
                    if e.get_attribute('data-spm'):
                        self.title = e.text

                if not self.title:
                    raise NoSuchElementException('天猫宝贝[ %s ]找不到标题 ....' % gid)

                logger.debug(u"    获取到【天猫】宝贝标题为 【%s】...." % self.title)
            else:  # 淘宝宝贝标题
                self.title = driver.find_element_by_class_name('tb-main-title').get_attribute("data-title")
                logger.debug(u"    获取到【淘宝】宝贝标题为 【%s】...." % self.title)

            try:  # 判断商品是否在售
                driver.find_element_by_class_name('J_LinkBuy')
                self.status = Goods.STATUS_SALING
            except NoSuchElementException:
                try:
                    driver.find_element_by_id('J_LinkBuy')
                except NoSuchElementException:
                    self.status = Goods.STATUS_UNSALE

        except NoSuchElementException:
            # TODO 判断商品是否已经删除
            if current_url.find('.taobao.com/market') == -1 and current_url.find('auction/noitem.htm') == -1:
                # raise GoodInfoUnknowError(u'获取标题未知异常...')
                self.status = Goods.STATUS_UNKNOWN
                pass
            else:
                self.status = Goods.STATUS_DELETE

    def naiveToSearch(self):

        driver = self.driver

        if self.title == None:
            raise ValueError('Goods Title Must bu set before navie to search.')

        logger.debug(u"    跳转到 搜索页面: %s" % SEARCH_URL)
        PageLoadAndRandomWait(driver, SEARCH_URL)
        inputElement = driver.find_element_by_id('q')
        inputElement.send_keys(self.title)
        btn = driver.find_element_by_class_name('btn-search')
        logger.debug(u"    等待页面跳转 ...")

        try:
            btn.submit()
        except TimeoutException:
            pass

    def __unicode__(self):
        return u'''
# NO. {seq:04d} |{id:^14s}|{where}|{status}|#############################
# 链接: {link}
# 标题: {title}
# 查找到: {totalCnt}
# 默认查询结果: {baseSearResult:s}
# 排序查询结果：{saleSearchResult:s}
        '''.format(
            seq=self.seq,
            id=self.gid,
            totalCnt=self.totalCnt,
            link=self.itemInfoUrl,
            where=unicode(self.where),
            title=unicode(self.title),
            status=unicode(self.status),
            baseSearResult=unicode(self.baseSearResult),
            saleSearchResult=unicode(self.saleSearchResult)
        )

    def getToFileStr(self):
        return u'''# NO. {seq:04d} |{id:>14s}|{where}|{status}|{totalCnt:>18s}|{baseSearResult:s}|{saleSearchResult:s}|'''.format(
            seq=self.seq,
            id=self.gid,
            totalCnt=unicode(self.totalCnt),
            link=unicode(self.itemInfoUrl),
            where=unicode(self.where),
            title=unicode(self.title),
            status=unicode(self.status),
            baseSearResult=unicode(self.baseSearResult.simpleResult()),
            saleSearchResult=unicode(self.saleSearchResult.simpleResult())
        )
