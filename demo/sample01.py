# coding: utf-8
import time
import urllib
import sys
import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0

SEARCH_URL = 'https://s.taobao.com/'

BASE_GOODS_URL = "https://item.taobao.com/item.htm?id="
URLS = [
    '524203651698',
    '520131971465',
    '527558742559',
    '527396611813',
    '526192650459',
    '528042588375',
    '527762331313',
    '526940979270',
    '521282982436',
    # '525551040687',
    '527692612118',
    '45850398513',
    '526936508736',
    # '26587820120',
]

URLS = [
 u'521893618096',
 u'523814861817',
 u'522155891308',
 u'521908735694',
 u'523999488662',
 u'521895708737',
 u'521729908117',
 u'521857135599', # 這個會卡主
 u'527048515751'
]


def get_ingore_time_out(driver, url, s):
    try:
        print(u"    访问超时设定(%s) %s" % (url, s))
        # driver.set_page_load_timeout(s)
        driver.get(url)
    except TimeoutException:
        print(u"    *** 页面加载超时, 直接跳过 ***")
        pass

def processOneGoods(driver, id):
    url = BASE_GOODS_URL + id
    print(u"\n\n********************[ID: %s]********************" % id)

    print(u"    跳转到 商品页面 【%s】...." % url)

    get_ingore_time_out(driver, url, 5)

    try:
        matchIndex = 0
        dealCnt = ""

        # 是否天猫商品判断
        if url != driver.current_url:
            items = driver.find_elements_by_tag_name('h1')
            for i in items:
                if i.get_attribute('data-spm'):
                    title = i.text

            if not title:
                raise NoSuchElementException()

        else:
            title = driver.find_element_by_class_name('tb-main-title').get_attribute("data-title")
        print(u"    获取到 商品标题为 【%s】...." % title)
        print(u"    跳转到 搜索页面: %s...." % SEARCH_URL)
        driver.get(SEARCH_URL)

        inputElement = driver.find_element_by_id('q')
        inputElement.send_keys(title)
        btn = driver.find_element_by_class_name('btn-search')
        print(u"    等待页面跳转 ...")
        btn.submit()

        print(u"    页面加载完成， 搜索商品 ...")
        # WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located)
        items = driver.find_elements_by_class_name('item ')
        matchItems = [i for i in items if i.get_attribute('data-category') == "auctions"]

        goodsItemId = 'J_Itemlist_PLink_%s' % id
        for i,item in enumerate(matchItems):

            try:
                item.find_element_by_id(goodsItemId)
                # 获取多少人购买
                dealCnt = item.find_element_by_class_name('deal-cnt').text
                matchIndex = i + 1

            except NoSuchElementException, e:
                continue

        if dealCnt:
            print(u"    *** [%s] 匹配到第 %s 个商品 【%s】 ***" % (id, matchIndex, dealCnt))
        else:
            print(u"    *** [%s] 【综合排序】第一页找不到该商品...")

        # nextUrl= re.sub('default$', 'sale-desc', driver.current_url)
        nextUrl = driver.current_url + '&sort=sale-desc'
        print(u"\n    跳转到按销量排序页面  ...")
        driver.get(nextUrl)

        print(u"    页面加载完成， 搜索商品 ...")
        items = driver.find_elements_by_class_name('item ')
        matchItems = [ i for i in items if i.get_attribute('data-category') == "auctions" ]

        goodsItemId = 'J_Itemlist_PLink_%s' % id
        for i, item in enumerate(matchItems):

            try:
                item.find_element_by_id(goodsItemId)
                # 获取多少人购买
                dealCnt = item.find_element_by_class_name('deal-cnt').text
                matchIndex = i + 1

            except NoSuchElementException, e:
                continue

        if dealCnt:
            print(u"    *** [%s] 匹配到第 %s 个商品 【%s】 ***" % (id, matchIndex, dealCnt))
        else:
            print(u"    *** [%s] 【销量排序】第一页找不到该商品...")

    except Exception, e:
        print(e)


def ProcessOneFile(file):


    pass


def ProcessDir(dirname):
    pass

def MainLoop():
    print(u"*** 打开浏览器 ***")
    # Create a new instance of the Firefox driver
    driver = webdriver.Firefox()
    driver.set_page_load_timeout(6)
    driver.set_script_timeout(6)
    driver.implicitly_wait(6)

    # go to the google home page
    print(u"*** 登录淘宝首页 ***")
    driver.get("https://www.taobao.com/")

    while True:

        try:
            # driver.find_element_by_class_name('login-info-nick')
            # time.sleep(1)
            print(u"Login Success...")
            [i for i in URLS if processOneGoods(driver, i)]

            # break
            print(u"退出登录...")

        except NoSuchElementException, e:
            print(u"You are did not Login .....")
            time.sleep(2)

    driver.quit()
    # raw_input(u"Press any key to quit .")
    raw_input(u"\n\n全部查找完成，按下任意键退出 .".encode('gbk'))
    time.sleep(1)

if __name__ == '__main__':
    MainLoop()