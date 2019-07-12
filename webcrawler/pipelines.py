# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import codecs
import re
from scrapy.exceptions import DropItem


class WebcrawlerPipeline(object):
    def process_item(self, item, spider):
        return item


class PricePipeline(object):
    def process_item(self, item, spider):
        price_pattern = re.compile("([0-9](\\w+ ?)*\\W+)")
        is_price = bool(re.search(price_pattern, item.get('price')))
        #spider.logger.info(item.get('price') + ' checked %s' % str(is_price))
        if is_price is True:
            return item
        else:
            raise DropItem('Missing item price in %s' % item)


class DuplicatesPipeline(object):

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['link'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(item['link'])
            return item


class JsonWriterPipeline(object):

    def open_spider(self, spider):
        self.file = codecs.open('%s_items.json' %
                                spider.name, 'w', encoding='utf-8')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item
