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

import pymongo

from woocommerce import API


class MongoPipeline(object):

    collection_name = "products"

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


class MySQLPipeline(object):

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
            price = parse_money(item["price"])
            brand = item['brand']
            rates = item['rates']

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

            #spider.logger.info('MySQL result: %s' % myresult)
            if myresult is None:
                query = 'INSERT INTO craw_products (category_id, title, short_description, swatch_colors, specifications, price, images, link, shop, domain_name,brand,rates) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
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
                    domain,
                    brand,
                    rates
                )
            else:
                query = 'UPDATE craw_products SET price=%s, last_update=now() WHERE id=%s'
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


class WoocommercePipeline(object):

    def __init__(self):
        try:
            self.wcapi = API(
                url="https://vivumuahang.com/",
                consumer_key="ck_e7b56c6e85a00b80b41605548c63aeb5cfa54868",
                consumer_secret="cs_83582ad6bcd50f08daef5e0033f1760582bd184a",
                version="wc/v3",
                timeout=60
            )
        except:
            raise Error(msg='Could not connect to Woocommerce API')

    def process_item(self, item, spider):
        """
        Product type. Options: simple, grouped, external and variable. Default is simple.
        """
        try:
            specifications = ' '.join(item["specifications"])
            # if item["specifications"] is not None:
            #     try:
            #         specifications = json.dumps(
            #             list(item["specifications"]), separators=(',', ':'), ensure_ascii=False)
            #     except:
            #         specifications = json.dumps(
            #             dict(item["specifications"]), separators=(',', ':'), ensure_ascii=False)
            #         pass
            price = parse_money(item["price"])
            short_description = item['description']
            images = [{'src': img} for img in item['images']]
            data = {
                "name": item['title'],
                "type": "external",
                "regular_price": price,
                "description": specifications,
                "short_description": short_description,
                "categories": [
                    {
                        "id": 70  # Smartphone
                    }
                ],
                "images": images,
                "external_url": item['link'],
                "tags": [
                    {"name": item['brand']},
                    {"name": item['shop']}
                ],
                "meta_data": [{'key': sp[0], 'value':sp[1]} for sp in item["specifications"]]
            }

            try:
                result = self.wcapi.post("products", data).json()
                if 'id' in result:
                    spider.logger.info(
                        'Successfull added a new product with Id: %s' % result['id'])
                else:
                    spider.logger.error(
                        'Insert product failed with errors: %s' % result)
            except ValueError as ex:
                spider.logger.error(
                        'Create new product failed with errors: {}'.format(ex))

            return item
        except:
            raise Error(msg='Could not insert new product by wcapi %s' % item)

        return None


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


def parse_money(value):
    if str(value).isdigit():
        return value
    return re.sub(r'[^\d]', '', str(value))
