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

        try:
            cat_id = item["cid"]
            title = item["title"]
            desc = item["description"]
            shop = item["shop"]
            link = item["link"]
            domain = item["domain"]
            price = self.parse_money(item["price"])

            query = 'SELECT id FROM craw_products WHERE category_id= %s and shop=%s and link=%s'
            params = (cat_id, shop, link)

            swatchcolors = []
            if item["swatchcolors"] is not None:
                try:
                    swatchcolors = json.dumps(
                        list(item["swatchcolors"]), separators=(',', ':'), ensure_ascii=False)
                except:
                    swatchcolors = json.dumps(
                        dict(item["swatchcolors"]), separators=(',', ':'), ensure_ascii=False)
                    pass

            specifications = []
            if item["specifications"] is not None:
                try:
                    specifications = json.dumps(
                        list(item["specifications"]), separators=(',', ':'), ensure_ascii=False)
                except:
                    specifications = json.dumps(
                        dict(item["specifications"]), separators=(',', ':'), ensure_ascii=False)
                    pass

            images = []
            if item["images"] is not None:
                images = json.dumps(list(item["images"]), ensure_ascii=False)

            self.mycursor.execute(query, params)
            myresult = self.mycursor.fetchone()
            if myresult is None:
                query = 'INSERT INTO craw_products (category_id, title, short_description, swatch_colors, specifications, price, images, link, shop, domain_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                params = (
                    cat_id,
                    title,
                    desc,
                    swatchcolors,
                    specifications,
                    price,
                    images,
                    link,
                    shop,
                    domain
                )
            else:
                query = 'UPDATE craw_products SET price = %s, last_update=now() WHERE id = %s'
                params = (price, myresult[0])

            self.mycursor.execute(query, params)
            self.db.commit()

            return item
        except Error as ex:
            self.db.rollback()
            raise Error('{} mysql query failed. {}'.format(spider.name, ex))

        return None

    def close_spider(self, spider):
        # closing database connection
        if(self.db.is_connected()):
            self.mycursor.close()
            self.db.close()
            spider.logger.info('MySQL connection is closed')

    def parse_money(self, value):
        return re.sub(r'[^\d]', '', value)


class PricePipeline(object):
    def process_item(self, item, spider):
        if item.get('price'):
            price_pattern = re.compile(r'\d+')
            is_price = bool(re.search(price_pattern, item.get('price')))
            # price = self.parse_money(item.get('price'))
            # spider.logger.info(item.get('price') + ' parsed to %s' % str(price))
            if is_price:
                return item
            else:
                raise DropItem('Missing item price in %s' % item['link'])
        else:
            raise DropItem('Missing item price in %s' % item['link'])


class DuplicatesPipeline(object):

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['link'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item['link'])
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


class FilesPipeline(object):
    def process_item(self, item, spider):

        save_path = 'files/%s' % spider.name

        try:
            import os
        except:
            raise ImportError('Could not find name in module')

        try:
            if item["images"] is None or len(item["images"]) <= 0:
                if not os.path.exists(save_path):
                    os.makedirs(save_path)

                page = item['link'].split('/')[-1]
                if not '.' in page:
                    filename = '%s.html' % page
                else:
                    filename = page
                path_file = os.path.join(save_path, filename)
                with open(path_file, 'w', encoding='utf-8') as html_file:
                    html_file.write(item["body"])
            else:
                pass

        except OSError as ex:
            spider.logger.info(
                '{} could not create directory.Errors: {}'.format(spider.name, ex))
            pass
        except Exception as ex:
            spider.logger.info(
                '{} could not save html to file.Errors: {}'.format(spider.name, ex))
            pass

        return item
