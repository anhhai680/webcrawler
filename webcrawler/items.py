# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose, TakeFirst, MapCompose, Join
from w3lib.html import remove_tags
import datetime


class WebcrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # visit_id = scrapy.Field()
    # visit_status = scrapy.Field()
    pass


class ProductItem(scrapy.Item):
    cid = scrapy.Field()  # Điện thoại, máy tính bảng, laptop...
    title = scrapy.Field()
    description = scrapy.Field()
    oldprice = scrapy.Field()
    price = scrapy.Field()
    swatchcolors = scrapy.Field()
    internalmemory = scrapy.Field()
    specifications = scrapy.Field()
    link = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()
    brand = scrapy.Field()  # Apple, Samsung, Xiaomi...
    shop = scrapy.Field()  # Shop name
    rates = scrapy.Field()
    location = scrapy.Field()
    domain = scrapy.Field()
    sku = scrapy.Field()
    instock = scrapy.Field()
    #freeshipping = scrapy.Field()
    body = scrapy.Field()
    created_date = scrapy.Field(serializer=str)
    last_updated = scrapy.Field(serializer=str)
    pass


clean_text = Compose(MapCompose(lambda v: v.strip()), Join())


class ProductLoader(ItemLoader):

    default_item_class = ProductItem

    cid_out = TakeFirst()

    title_out = clean_text

    description_out = clean_text

    oldprice_out = TakeFirst()
    price_out = TakeFirst()

    swatchcolors_out = TakeFirst()
    internalmemory_out = TakeFirst()

    link_out = clean_text
    brand_out = clean_text
    shop_out = clean_text
    rates_out = clean_text
    location_out = clean_text
    domain_out = TakeFirst()
    sku_out = clean_text
    instock_out = TakeFirst()
    #freeshipping_out = TakeFirst()
    body_out = TakeFirst()

    pass


def filter_price(value):
    if value.isdigit():
        return value
