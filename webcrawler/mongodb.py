import pymongo
from scrapy.exceptions import DropItem


class MongoPipeline(object):

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        try:
            self.client = pymongo.MongoClient(self.mongo_uri)
            self.db = self.client[self.mongo_db]
            self.collection_name = "crawl_products"
            colllist = self.db.list_collection_names()
            if self.collection_name in colllist:
                spider.logger.info('%s has been connected.' %
                                   self.collection_name)
        except:
            raise pymongo.errors.PyMongoError(
                'Could not open mongodb connection from %s' % self.mongo_db)

    def process_item(self, item, spider):
        try:
            # self.db[self.collection_name].insert(list(item))
            myquery = {'link': item['link']}
            mycol = self.db[self.collection_name].count(myquery)
            if mycol is not None:
                self.db[self.collection_name].insert_one(dict(item))
        except pymongo.errors.InvalidBSON as ex:
            spider.logger.error('InvalidBSON %s' % ex)
        return item
