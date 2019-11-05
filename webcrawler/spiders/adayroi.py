# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import re
from scrapy.selector import Selector

from ..items import ProductItem

logger = logging.getLogger(__name__)


class AdayroiSpider(scrapy.Spider):
    name = 'adayroi'
    allowed_domains = ['adayroi.vn']
    start_urls = [
        'https://rest.adayroi.com/cxapi/v2/adayroi/search?q=&categoryCode=323&pageSize=32']

    def __init__(self, limit_pages=None, *a, **kw):
        super(AdayroiSpider, self).__init__(*a, **kw)
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 300

    def parse(self, response):
        logger.info('Scrape url: %s' % response.url)
        sel = Selector(response, type="xml")
        if sel is not None:
            for item in sel.xpath('//productSearchPage/products').getall():
                product_title = item.xpath('.//name/text()').get()
                product_description = item.xpath('.//description/text()').get()

                oldprice = item.xpath(
                    './/productPrice/value/text()').get()
                product_oldprice = self.parse_money(oldprice)

                price = item.xpath('.//price/value/text()').get()
                product_price = self.parse_money(price)

                product_swatchcolors = []
                for color in item.xpath('.//firstCategoryNameList').getall():
                    color_name = color.xpath('.//spCategoryName/text()').get()
                    if 'Màu sắc' in color_name:
                        color_item = ''
                        color_value = ''
                product_internalmemory = None
                product_specifications = None
                product_images = None
                plink = sel.xpath('.//url/text()').get()
                product_link = 'https://adayroi.vn%s' % plink
                product_brand = item.xpath('.//brandName/text()').get()
                product_shop = item.xpath(
                    './/merchant/merchantName/text()').get()
                product_rates = 0
                product_location = 'Hồ Chí Minh'
                product_sku = item.xpath('.//productSKU/text()').get()
                product_instock = 1
        pass

    def parse_money(self, value):
        if str(value).isdigit():
            return value
        return re.sub(r'[^\d]', '', str(value))
