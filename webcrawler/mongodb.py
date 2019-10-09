import pymongo
from scrapy.exceptions import DropItem


class MongoPipeline(object):

    collection_name = "crawl_products"

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
            colllist = self.db.list_collection_names()
            if collection_name in colllist:
                spider.logger.info('%s has been connected.' % collection_name)
        except:
            spider.logger.error(
                'Could not open mongodb connection from %s' % self.mongo_db)

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        try:
            # specifications = None
            # if item["specifications"] is not None:
            #     try:
            #         specifications = json.dumps(
            #             list(item["specifications"]), separators=(',', ':'), ensure_ascii=False)
            #     except:
            #         specifications = json.dumps(
            #             dict(item["specifications"]), separators=(',', ':'), ensure_ascii=False)
            #         pass
            # item["specifications"] = specifications
            # self.db[self.collection_name].insert(list(item))
            self.db[self.collection_name].insert_one(dict(item))
        except pymongo.errors.InvalidBSON as ex:
            spider.logger.error('InvalidBSON %s' % ex)
        return item
