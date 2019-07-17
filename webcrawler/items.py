# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class WebcrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # visit_id = scrapy.Field()
    # visit_status = scrapy.Field()
    
    pass

class ProductItem(scrapy.Item):
    title = scrapy.Field()
    cid = scrapy.Field()
    description = scrapy.Field()
    price = scrapy.Field()
    swatchcolors = scrapy.Field()
    specifications = scrapy.Field()
    link = scrapy.Field()
    images = scrapy.Field()
    #brand = scrapy.Field()
    shop = scrapy.Field()
    domain = scrapy.Field()
    #last_updated = scrapy.Field(serializer=str)
    pass
