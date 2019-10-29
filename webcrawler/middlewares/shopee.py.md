from scrapy import signals
from scrapy.http import Request
from scrapy.http import HtmlResponse
from scrapy.item import BaseItem
from scrapy.utils.request import request_fingerprint
from scrapy.exceptions import DontCloseSpider
import re


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ShopeeSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_idle, signal=signals.spider_idle)
        return s

    def spider_idle(self, spider):
        spider.logger.info('===> Spider idle: %s.' % spider.name)

        spider.logger.info('I am alive. Request more data...')
        # spider.crawler.engine.crawl(spider.create_more_requests(), spider)
        reqs = spider.start_requests()
        if not reqs:
            return
        for req in reqs:
            spider.crawler.engine.schedule(req, spider)
        raise DontCloseSpider


class ShopeeSpiderDownloaderMiddleware(object):

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
        pass

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.
        shopee_pattern = re.compile(r'^https://shopee.vn/(.*?)$')
        if bool(re.search(shopee_pattern, request.url)) is False:
            return None

        options = webdriver.ChromeOptions()

        prefs = {'profile.managed_default_content_settings.images': 2}
        options.add_experimental_option('prefs', prefs)

        options.add_argument('headless')
        options.add_argument("--disable-notifications")
        options.add_argument("--incognito")
        options.add_argument("--disable-extensions")
        options.add_argument(" --disable-gpu")
        options.add_argument(" --disable-infobars")
        options.add_argument(" -–disable-web-security")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(chrome_options=options)
        driver.get(request.url)
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//link[@rel="canonical"]/@href'))
            )
        except:
            spider.logger.info('WebDriver exception: %s' %
                               driver.current_url)
        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        body = driver.page_source
        return HtmlResponse(driver.current_url, body=body, encoding='utf-8', request=request)

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        # driver.close()
        pass

    def spider_closed(self, spider):
        # driver.close()
        # driver.quit()
        pass
