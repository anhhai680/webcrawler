import pymongo


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
            self.db[self.collection_name].insert(list(item))
        except pymongo.errors.InvalidBSON as ex:
            spider.logger.error('InvalidBSON %s' % ex)
        return item
