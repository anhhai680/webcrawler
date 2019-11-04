import pymongo
from scrapy.exceptions import DropItem
import datetime


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
            mycol = self.db[self.collection_name].count_documents(myquery)

            # set datetime value
            item['created_date'] = datetime.datetime.now()
            item['last_updated'] = datetime.datetime.now()

            if mycol <= 0:
                self.db[self.collection_name].insert_one(dict(item))
            else:
                newcol = {'$set': {
                    'oldprice': item['oldprice'], 'price': item['price'], 'rates': item['rates'], 'instock': item['instock'], 'last_updated': item['last_updated']}}
                self.db[self.collection_name].update_one(myquery, newcol)
        except pymongo.errors.InvalidBSON as ex:
            spider.logger.error('InvalidBSON %s' % ex)
        return item
