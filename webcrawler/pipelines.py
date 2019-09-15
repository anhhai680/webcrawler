# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exporters import JsonItemExporter
import json
import codecs
import re
from scrapy.exceptions import DropItem, NotConfigured

import mysql.connector
from mysql.connector import Error


class MySQLPipeline(object):

    def __init__(self, host, user, passwd, db):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.db = db

    @classmethod
    def from_crawler(cls, crawler):
        """
        Get all database infomations from settings
        """
        db_settings = crawler.settings.getdict("DB_SETTINGS")
        if not db_settings:
            raise NotConfigured
        host = db_settings["host"]
        user = db_settings["user"]
        passwd = db_settings["passwd"]
        db = db_settings["db"]
        return cls(host, user, passwd, db)

    def open_spider(self, spider):
        """
        Initializes database connection and sessionmaker.
        Creates deals table.
        """
        try:
            # self.db = mysql.connector.connect(
            #     host="localhost",
            #     user="root",
            #     passwd="Admin@123",
            #     database="ecrawdb",
            #     collation='utf8mb4_unicode_ci',
            #     charset='utf8',
            #     use_unicode=True
            # )
            self.db = mysql.connector.connect(
                host=self.host,
                user=self.user,
                passwd=self.passwd,
                database=self.db,
                # collation='utf8mb4_unicode_ci',
                charset='utf8',
                use_unicode=True
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
            swatchcolors = None
            specifications = None
            oldprice = parse_money(item["oldprice"])
            price = parse_money(item["price"])
            link = item["link"]
            brand = item['brand']
            shop = item["shop"]
            location = item['location']
            domain = item["domain"]
            rates = item['rates']
            instock = 1 if item['instock'] == 'True' else 0
            shipping = item['shipping']

            query = 'SELECT id FROM crawl_products WHERE category_id= %s and domain=%s and link=%s'
            params = (cat_id, domain, link)

            if item["swatchcolors"] is not None:
                try:
                    swatchcolors = json.dumps(
                        list(item["swatchcolors"]), separators=(',', ':'), ensure_ascii=False)
                except:
                    swatchcolors = json.dumps(
                        dict(item["swatchcolors"]), separators=(',', ':'), ensure_ascii=False)
                    pass

            if item["specifications"] is not None:
                try:
                    specifications = json.dumps(
                        list(item["specifications"]), separators=(',', ':'), ensure_ascii=False)
                except:
                    specifications = json.dumps(
                        dict(item["specifications"]), separators=(',', ':'), ensure_ascii=False)
                    pass

            images = None
            if item["images"] is not None:
                images = json.dumps(list(item["images"]), ensure_ascii=False)

            self.mycursor.execute(query, params)
            myresult = self.mycursor.fetchone()

            #spider.logger.info('MySQL result: %s' % myresult)
            if myresult is None:
                query = 'INSERT INTO crawl_products (category_id, title, short_description, swatch_colors, specifications, oldprice, price, images, link, brand, shop, location, domain, rates, instock,shipping) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s)'
                params = (cat_id, title, desc, swatchcolors, specifications, oldprice, price,
                          images, link, brand, shop, location, domain, rates, instock, shipping)
            else:
                id = myresult[0]
                query = 'UPDATE crawl_products SET oldprice=%s,price=%s,last_update=now(),instock=%s WHERE id=%s'
                params = (oldprice, price, instock, id)

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


class PricePipeline(object):
    def process_item(self, item, spider):
        if item.get('price'):
            # price_pattern = re.compile(r'\d+')
            # is_price = bool(re.search(price_pattern, item.get('price')))
            price = parse_money(item.get('price'))
            # spider.logger.info(item.get('price') + ' parsed to %s' % str(price))
            if price is not None:
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
        self.file = codecs.open('%s_links.jl' %
                                spider.name, 'w', encoding='utf-8')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        #line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        line = item['link'] + "\n"
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


class JsonDataPipeline(object):
    def __init__(self):
        # self.file = open("data_export.json", 'wb')
        # self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        # self.exporter.start_exporting()
        pass

    def open_spider(self, spider):
        self.file = open("%s_data.json" % spider.name, 'wb')
        self.exporter = JsonItemExporter(
            self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


def parse_money(value):
    if str(value).isdigit():
        return value
    return re.sub(r'[^\d]', '', str(value))
