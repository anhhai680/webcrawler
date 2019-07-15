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
    dowload_delay = 1
    start_urls = [
        'https://www.sendo.vn/m/wap_v2/category/product?category_id=2354&listing_algo=algo5&p=1&platform=web&s=60&sortType=default_listing_desc',
    ]

    def parse(self, response):
        logger.info('Parsing Url: %s', response.url)
        try:
            json_data = json.loads(response.body, encoding='utf-8')
            if json_data is not None:
                data = json_data["result"]["data"]
                logger.info('There is a total of ' +
                            str(len(data)) + ' items.')
                if len(data) > 0:
                    for item in data:
                        path = item["cat_path"]
                        if path is not None:
                            url_key = path.split('.html/')[0]
                            # An example link: https://www.sendo.vn/m/wap_v2/full/san-pham/samsung-galaxy-s7-edge-13399478?platform=web
                            product_link = 'https://www.sendo.vn/m/wap_v2/full/san-pham/' + \
                                url_key + '?platform=web'
                            yield response.follow(product_link, callback=self.parse_product_detail)

                # Following pagination to scrape next page
                total_pages = int(json_data["result"]["meta_data"]["total_page"])
                page_number = 1
                logger.info('There is a total of ' +
                            str(total_pages) + ' links.')
                while page_number <= total_pages:
                    try:
                        page_number += 1
                        # https://www.sendo.vn/m/wap_v2/category/product?category_id=2354&listing_algo=algo5&p=1&platform=web&s=60&sortType=default_listing_desc
                        next_page = 'https://www.sendo.vn/m/wap_v2/category/product?category_id=2354&listing_algo=algo5&p=%s&platform=web&s=60&sortType=default_listing_desc' % page_number
                        yield response.follow(next_page, callback=self.parse)
                    except:
                        logger.error(
                            'Could not follow to next page %s', page_number)
                        break
        except ValueError as ex:
            logger.error('Could not load json data with errors %s', ex)
            pass

    def parse_product_detail(self, response):
        logger.info('Product Url: %s', response.url)
        try:
            json_data = json.loads(response.body, encoding='utf-8')
            if json_data is not None:
                data = json_data["result"]["data"]
                if len(data) > 0:
                    product_title = str(data["name"]).strip()
                    product_desc = str(data["short_description"]).strip()
                    product_price = str(data["final_price"])
                    product_images = [item["image"] for item in data["media"] if item["type"] == 'image']
                    product_swatchcolors = [att["name"]
                                            for att in data["attribute"][0]["value"]]
                    product_link = 'https://www.sendo.vn/' + data["cat_path"]
                    product_specifications = []

                    # str_list = list(filter(None, str_list))
                    sel = Selector(text=data["description"])
                    for st in sel.xpath('//div[@class="attrs-block"]/ul/li'):
                        if st is not None:
                            key = st.xpath('.//strong/text()').get().strip()
                            if key is None or key == '.':
                                break
                            value = st.xpath('.//span/text()').get().strip()
                            if value is None or value == '.':
                                break
                            product_specifications.append({key, value})

                    products = ProductItem()
                    products['title'] = product_title
                    products['description'] = product_desc
                    products['price'] = product_price
                    products['swatchcolors'] = product_swatchcolors
                    products['specifications'] = product_specifications
                    products['link'] = product_link
                    products['images'] = product_images
                    products['last_updated'] = datetime.now()
                    yield products

        except:
            logger.error('Parse %s product failed.', response.url)
            pass
