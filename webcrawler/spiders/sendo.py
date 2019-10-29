# -*- coding: utf-8 -*-
import scrapy
import logging
import re
import json
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector
from datetime import datetime


from ..items import ProductItem

logger = logging.getLogger(__name__)


class SendoSpider(scrapy.Spider):
    name = 'sendo'
    allowed_domains = ['www.sendo.vn']
    #dowload_delay = 1
    start_urls = [
        'https://www.sendo.vn/m/wap_v2/category/product?category_id=2354&listing_algo=algo5&p=1&platform=web&s=60&sortType=default_listing_desc',
    ]

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'webcrawler.middlewares.sendo.SendoSpiderMiddleware': 543
        },
    }

    def __init__(self, limit_pages=None, *a, **kw):
        super(SendoSpider, self).__init__(*a, **kw)
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 300

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
                            # https://www.sendo.vn/m/wap_v2/full/san-pham/samsung-galaxy-s7-edge-13399478?platform=web
                            product_link = 'https://www.sendo.vn/m/wap_v2/full/san-pham/' + \
                                url_key + '?platform=web'
                            yield response.follow(product_link, callback=self.parse_product_detail)

                # Following pagination to scrape next page
                total_pages = int(
                    json_data["result"]["meta_data"]["total_page"])
                page_number = 1
                logger.info('There is a total of ' +
                            str(total_pages) + ' links.')
                while page_number <= total_pages:
                    if page_number > self.limit_pages:
                        break
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
                    product_price = 0
                    if 'special_price' in data:
                        product_price = data["special_price"]
                    else:
                        product_price = data['final_price']

                    product_images = [item["image"]
                                      for item in data["media"] if item["type"] == 'image']

                    product_swatchcolors = []
                    # swatchcolors = [att["name"]
                    #                 for att in data["attribute"][0]["value"]]
                    for att in data['attribute']:
                        if att['attribute_id'] == 284:  # Màu sắc
                            for opt in att['value']:
                                name = opt['name']
                                opt_id = str(opt['option_id'])
                                for varitem in data['variants']:
                                    if varitem['attribute_hash'] == opt_id or opt_id in varitem['attribute_hash']:
                                        price = varitem['price']
                                        special_price = 0
                                        if 'special_price' in varitem:
                                            special_price = varitem['special_price']
                                        else:
                                            special_price = varitem['final_price']

                                        stock = varitem['stock']
                                        swatchcolors = {'name': name, 'value': {
                                            'price': price,
                                            'special_price': special_price,
                                            'stock': stock}
                                        }
                                        product_swatchcolors.append(
                                            swatchcolors)

                    product_link = 'https://www.sendo.vn/' + data["cat_path"]

                    # str_list = list(filter(None, str_list))
                    # for st in sel.xpath('//div[@class="attrs-block"]/ul/li'):
                    #     if st is not None:
                    #         key = st.xpath('.//strong/text()').get().strip()
                    #         if key is None or key == '.':
                    #             break
                    #         value = st.xpath('.//span/text()').get().strip()
                    #         if value is None or value == '.':
                    #             break
                    #         product_specifications.append({key, value})

                    product_specifications = []
                    sel = Selector(text=data["description"])
                    names = sel.xpath(
                        '//div[@class="attrs-block"]/ul/li/strong/text()').getall()
                    values = sel.xpath(
                        '//div[@class="attrs-block"]/ul/li/span/text()').getall()
                    if len(names) > 0:
                        for index in range(len(names)):
                            if values[index] is not None and values[index] != '':
                                product_specifications.append(
                                    [names[index], values[index]])

                    product_oldprice = data['final_price_max']
                    product_internalmemory = sel.xpath(
                        '//div[@class="attrs-block"]/ul/li/strong[contains(text(),"Bộ nhớ trong")]/../span/text()').get().strip()
                    if product_internalmemory is not None:
                        product_internalmemory = product_internalmemory.replace(
                            '.', '')

                    product_brand = sel.xpath(
                        '//div[@class="attrs-block"]/ul/li/strong[contains(text(),"Hãng sản xuất")]/../span/text()').get().strip()
                    if product_brand is not None:
                        product_brand = product_brand.replace('.', '')

                    product_shop = str(data['shop_info']['shop_name'])
                    product_location = str(
                        data['shop_info']['warehourse_region_name'])
                    product_rates = data['shop_info']['rating_avg']
                    product_sku = str(data['sku'])
                    product_instock = 1
                    instock = data['stock_status']
                    if instock != 1:
                        product_instock = 0

                    products = ProductItem()
                    products['cid'] = 'dienthoai'  # 1: Smartphone
                    products['title'] = product_title
                    products['description'] = product_desc
                    products['oldprice'] = product_oldprice
                    products['price'] = product_price
                    products['swatchcolors'] = product_swatchcolors
                    products['internalmemory'] = product_internalmemory
                    products['specifications'] = product_specifications
                    products['link'] = product_link
                    products['images'] = product_images
                    products['brand'] = product_brand
                    products['shop'] = product_shop
                    products['rates'] = product_rates
                    products['location'] = product_location
                    products['domain'] = 'sendo.vn'
                    products['sku'] = product_sku
                    products['instock'] = product_instock
                    products['body'] = ''

                    yield products

        except:
            logger.error('Parse %s product failed.', response.url)
            pass

    def parse_money(self, value):
        if str(value).isdigit():
            return value
        return re.sub(r'[^\d]', '', str(value))
