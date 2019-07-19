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
from mysql.connector import Error

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
            self.db = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="Admin@123",
                database="ecrawdb",
                collation='utf8mb4_unicode_ci'
            )
            if self.db.is_connected():
                self.mycursor = self.db.cursor(buffered=True)
        except Error as ex:
            raise ConnectionError('Error while connecting to MySQL', ex)

    def process_item(self, item, spider):
        """Save deals in the database.
        This method is called for every item pipeline component.
        """

        cat_id = item["cid"]
        shop = item["shop"]
        link = item["link"]
        domain = item["domain"]
        price = item["price"]

        query = 'SELECT id FROM craw_products WHERE category_id= %s and shop=%s and link=%s'
        params = (cat_id, shop, link)

        try:
            self.mycursor.execute(query, params)
            myresult = self.mycursor.fetchone()
            if myresult is None:
                query = 'INSERT INTO craw_products (category_id, title, short_description, swatch_colors, specifications, price, images, link, shop, domain_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                params = (
                    item["cid"],
                    item["title"],
                    item["description"],
                    json.dumps(list(item["swatchcolors"]), ensure_ascii=False),
                    json.dumps(dict(item["specifications"]),
                               ensure_ascii=False),
                    price,
                    json.dumps(list(item["images"]), ensure_ascii=False),
                    link,
                    shop,
                    domain
                )
            else:
                query = 'UPDATE craw_products SET price = %s WHERE id = %s'
                params = (price, myresult[0])
        except Error as ex:
            spider.logger.info(
                '{} mysql query failed. {}'.format(spider.name, ex))
            pass

        try:
            self.mycursor.execute(query, params)
            self.db.commit()
        except Error as ex:
            self.db.rollback()
            spider.logger.info(
                '{} mysql query failed. {}'.format(spider.name, ex))
            raise

        return item

    def close_spider(self, spider):
        # closing database connection
        if(self.db.is_connected()):
            self.mycursor.close()
            self.db.close()
            spider.logger.info('MySQL connection is closed')


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
