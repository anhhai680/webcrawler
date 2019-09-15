from scrapy import signals
from scrapy.http import Request
from scrapy.http import HtmlResponse
from scrapy.item import BaseItem
from scrapy.utils.request import request_fingerprint
from scrapy.exceptions import DontCloseSpider, NotConfigured, IgnoreRequest

import mysql.connector
from mysql.connector import Error


class LazadaSpiderMiddleware(object):

    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.
    def __init__(self, host, user, passwd, db):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.db = db

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        db_settings = crawler.settings.getdict("DB_SETTINGS")
        if not db_settings:
            raise NotConfigured
        host = db_settings["host"]
        user = db_settings["user"]
        passwd = db_settings["passwd"]
        db = db_settings["db"]
        s = cls(host, user, passwd, db)
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
        spider.logger.info('Spider request: %s' % request)
        if request in self.blacklinks:
            raise IgnoreRequest
        return None

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chains
        pass

    def spider_opened(self, spider):
        """
        Initializes database connection and sessionmaker.
        Creates deals table.
        """
        try:
            self.db = mysql.connector.connect(
                host=self.host,
                user=self.user,
                passwd=self.passwd,
                database=self.db,
                charset='utf8',
                use_unicode=True
            )
            if self.db.is_connected():
                self.mycursor = self.db.cursor(buffered=True)
                query = 'SELECT link FROM crawl_blacklinks WHERE domain="lazada.vn"'
                params = 'lazada.vn'
                self.mycursor.execute(query)
                myresult = self.mycursor.fetchall()
                spider.logger.info('There is total %s of items' %
                                   len(myresult))
                if len(myresult) > 0:
                    self.blacklinks = myresult
            else:
                raise ConnectionError('Could not connect to MySQL')

        except Error as ex:
            raise ConnectionError('Error while connecting to MySQL', ex)
        spider.logger.info('Spider opened: %s' % spider.name)
