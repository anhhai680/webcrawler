from scrapy import signals
from scrapy.http import Request
from scrapy.http import HtmlResponse
from scrapy.item import BaseItem
from scrapy.utils.request import request_fingerprint
from scrapy.exceptions import DontCloseSpider


class LazadaSpiderMiddleware(object):

    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
