# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags


class WebcrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # visit_id = scrapy.Field()
    # visit_status = scrapy.Field()
    pass


class ProductItem(scrapy.Item):
    cid = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    price = scrapy.Field()
    swatchcolors = scrapy.Field()
    specifications = scrapy.Field()
    link = scrapy.Field()
    images = scrapy.Field()
    brand = scrapy.Field() # Apple, Samsung, Xiaomi...
    shop = scrapy.Field() # Shop name
    domain = scrapy.Field()
    rates = scrapy.Field()
    #last_updated = scrapy.Field(serializer=str)   
    body = scrapy.Field()
    pass


class ProductLoader(ItemLoader):
    default_item_class = ProductItem()

    cid_out = TakeFirst()

    title_in = MapCompose(remove_tags)
    title_out = Join()

    description_in = MapCompose(remove_tags)
    description_out = Join()

    price_out = TakeFirst()
    link_out = TakeFirst()
    shop_out = TakeFirst()
    domain_out = TakeFirst()
    body_out = TakeFirst()
    pass


def filter_price(value):
    if value.isdigit():
        return value
