from scrapy import signals
from scrapy.http import Request
from scrapy.http import HtmlResponse
from scrapy.item import BaseItem
from scrapy.utils.request import request_fingerprint
from scrapy.exceptions import DontCloseSpider, NotConfigured, IgnoreRequest

import pymongo


class ShopeeSpiderMiddleware(object):

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):

        MONGO_URI = crawler.settings.get('MONGO_URI')
        MONGO_DATABASE = crawler.settings.get('MONGO_DATABASE')
        if MONGO_URI is None or MONGO_DATABASE is None:
            raise NotConfigured('{0} or {1} did not defined in settings.'.format(
                MONGO_URI, MONGO_DATABASE))

        s = cls(
            mongo_uri=MONGO_URI,
            mongo_db=MONGO_DATABASE
        )
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        try:
            self.client = pymongo.MongoClient(self.mongo_uri)
            self.db = self.client[self.mongo_db]
            self.collection_name = "crawl_blacklinks"
            self.blacklinks = []
            colllist = self.db.list_collection_names()
            if self.collection_name in colllist:
                spider.logger.info('%s has been connected.' %
                                   self.collection_name)
                query = {'domain': 'shopee.vn'}
                projection = {'link': 1, '_id': 0}
                mycol = self.db[self.collection_name]
                mydocs = list(mycol.find(query, projection))
                if len(mydocs) > 0:
                    self.blacklinks = mydocs
                spider.logger.info('{0} query results {1}'.format(
                    self.collection_name, len(mydocs)))

        except:
            raise pymongo.errors.PyMongoError(
                'PyMongo could not open collection %s' % self.collection_name)

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        spider.logger.info('Url request: {0}'.format(request.url))

        try:
            if len(self.blacklinks) > 0:
                for item in self.blacklinks:
                    if request.url in item['link']:
                        raise IgnoreRequest('IgnoreRequest %s' % request.url)
            else:
                spider.logger.info('Shopee blacklinks have no any records.')
        except Exception as ex:
            spider.logger.error(
                'Shopee spider process_request errors: {}'.format(ex))

        return None
