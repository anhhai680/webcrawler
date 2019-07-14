# -*- coding: utf-8 -*-
import scrapy
import logging
import re
import json
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.selector import Selector
from datetime import datetime


from ..items import ProductItem

logger = logging.getLogger(__name__)


class SendoSpider(scrapy.Spider):
    name = 'sendo'
    allowed_domains = ['www.sendo.vn']
    start_urls = [
        'https://www.sendo.vn/m/wap_v2/category/product?category_id=2354&listing_algo=algo5&p=1&platform=web&s=60&sortType=default_listing_desc',
        # 'https://www.sendo.vn/iphone/'
    ]

    def parse(self, response):
        logger.info('Parsing Url: %s', response.url)
        try:
            json_data = json.loads(response, encoding='utf-8')
            if json_data is not None:
                data = json_data["result"]["data"]
                logger.info('There is a total of ' +
                            str(len(data)) + ' items.')
                if len(data) > 0:
                    for product_link in data["url_key"]:
                        product_link = 'https://www.sendo.vn/m/wap_v2/full/san-pham/' + product_link + '?platform=web'
                        yield response.follow(product_link, callback=self.parse_product_detail)

                # Following pagination to scrape next page
                total_pages = int(json_data["meta_data"]["total_page"])
                page_number = 1
                logger.info('There is a total of ' + str(total_pages) + ' links.')
                while page_number <= total_pages:
                    page_number += 1
                    next_page = 'https://www.sendo.vn/m/wap_v2/category/product?category_id=2354&listing_algo=algo5&p=%s&platform=web&s=60&sortType=default_listing_desc' % page_number
                    yield response.follow(next_page, callback=self.parse)
        except:
            logger.error('Cannot load json data. Errors')
            pass

    def parse_product_detail(self, response):
        logger.info('Product Url: %s', response.url)
        try:
            json_data = json.loads(response, encoding='utf-8')
            if json_data is not None:
                data = json_data["result"]["data"]
                if len(data) > 0:
                    name = data["name"]
                    description = data["description"]
                    price = data["price"]
                    images = [item["image"] for item in data["media"]]
        except:
            pass
