# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import codecs
import re
from scrapy.exceptions import DropItem
import mysql.connector

# from sqlalchemy.orm import sessionmaker
# from webcrawler.models import EcrawlDB, db_connect, create_table


# class WebcrawlerPipeline(object):
#     def __init__(self):
#         """
#         Initializes database connection and sessionmaker.
#         Creates deals table.
#         """
#         engine = db_connect()
#         create_table(engine)
#         self.Session = sessionmaker(bind=engine)

#     def process_item(self, item, spider):
#         """Save deals in the database.
#         This method is called for every item pipeline component.
#         """
#         session = self.Session()
#         db = EcrawlDB()
#         db.title = item["title"]
#         db.cid = item["cid"]
#         db.description = item["description"]
#         db.swatchcolors = item["swatchcolors"]
#         db.specifications = item["specifications"]
#         db.images = item["images"]
#         db.price = item["price"]
#         db.link = item["link"]
#         #db.brand = item["brand"]
#         db.shop = item["shop"]
#         db.domain = item["domain"]
#         #db.last_update = item["last_update"]

#         try:
#             session.add(db)
#             session.commit()
#         except:
#             session.rollback()
#             raise
#         finally:
#             session.close()

#         return item


class WebcrawlerPipeline(object):
    def __init__(self):
        """
        Initializes database connection and sessionmaker.
        Creates deals table.
        """
        try:
            self.mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="Admin@123",
                database="ecrawdb"
            )
            self.mycursor = self.mydb.cursor()
        except Exception:
            raise

    def process_item(self, item, spider):
        """Save deals in the database.
        This method is called for every item pipeline component.
        """
        sql = 'INSERT INTO craw_products (category_id, title, short_description, swatch_colors, specifications, price, images, link, shop, domain_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        val = (
            item["cid"],
            item["title"],
            item["description"],
            item["swatchcolors"],
            item["specifications"],
            item["price"],
            item["images"],
            item["link"],
            item["shop"],
            item["domain"]
        )

        try:
            self.mycursor.execute(sql, val)
            self.mydb.commit()
        except:
            self.mydb.rollback()
            raise
        finally:
            self.mydb.close()

        return item


class PricePipeline(object):
    def process_item(self, item, spider):
        #price_pattern = re.compile("([0-9](\\w+ ?)*\\W+)")
        price_pattern = re.compile(r'\d+')
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
