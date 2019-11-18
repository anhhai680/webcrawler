# -*- coding: utf-8 -*-
import scrapy
import logging
import re
import json

from ..items import ProductItem

logger = logging.getLogger(__name__)


class ShopeeSpider(scrapy.Spider):
    name = 'shopee'
    allowed_domains = ['shopee.vn']
    # start_urls = [l.strip() for l in open('shopee_links.jl').readlines()]
    # start_urls = ['https://shopee.vn/smartphone-cat.84.1979.19042']
    start_urls = [
        'https://shopee.vn/api/v2/search_items/?by=relevancy&keyword=smartphone&limit=100&match_id=19042&newest=0&order=desc&page_type=search']

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'webcrawler.middlewares.shopee.ShopeeSpiderMiddleware': 543
        },
    }

    def __init__(self, limit_pages=None, *args, **kwargs):
        super(ShopeeSpider, self).__init__(*args, **kwargs)
        self.page_number = 0
        self.total_records = 0
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 300

    def parse(self, response):
        logger.info('Scrape Url: %s', response.url)
        json_data = json.loads(response.body, encoding='utf-8')
        if json_data is not None:
            items = json_data['items']
            if items is not None:
                if len(items) > 0:
                    # Get itemid and shopid from items list
                    product_link = 'https://shopee.vn/api/v2/item/get?itemid={}&shopid={}'
                    data = [product_link.format(item['itemid'], item['shopid'])
                            for item in items]
                    for url in data:
                        # yield scrapy.Request(url, callback=self.parse_product_detail)
                        yield response.follow(url, callback=self.parse_product_detail)
            else:
                self.limit_pages = 0  # Stop at the end of link

        # Make a next page link to continues scrape
        next_page_url = 'https://shopee.vn/api/v2/search_items/?by=relevancy&keyword=smartphone&limit=100&match_id=19042&newest={}&order=desc&page_type=search'
        if self.page_number <= self.limit_pages:
            self.total_records += 50
            next_page = next_page_url.format(self.total_records)
            logger.info('Next page: %s', next_page)
            # yield scrapy.Request(next_page, callback=self.parse)
            yield response.follow(next_page, callback=self.parse)
            self.page_number += 1
        pass

    def parse_product_detail(self, response):
        logger.info('Product Url: %s', response.url)
        try:
            json_data = json.loads(response.body, encoding='utf-8')
            if json_data is not None:
                item = json_data['item']
                if item is not None:
                    product_title = str(item['name']).strip()
                    product_desc = str(item['description']).strip()
                    product_price = self.parse_money(item['price'])/100000
                    # product_swatchcolors = [{mod['name'], str(mod['price'])}
                    #                         for mod in item['models'] if item['models']]
                    product_swatchcolors = []
                    if len(item['models']) > 0:
                        for mod in item['models']:
                            name = mod['name']
                            price = self.parse_money(mod['price'])/100000
                            stock = mod['stock']
                            swatchcolors = {'name': name, 'value': {
                                'price': price,
                                'stock': stock
                            }}
                            product_swatchcolors.append(swatchcolors)

                    image_link = 'https://cf.shopee.vn/file/{}'
                    product_images = [image_link.format(
                        src) for src in item['images'] if item['images']]
                    product_specifications = [[attr['name'], attr['value']]
                                              for attr in item['attributes'] if item['attributes']]
                    product_link = 'https://shopee.vn/{}-i.{}.{}'.format(
                        product_title, item['shopid'], item['itemid'])

                    product_oldprice = self.parse_money(
                        item['price_before_discount'])/100000
                    product_internalmemory = None
                    if len(item['attributes']) > 0:
                        for attr in item['attributes']:
                            if attr['id'] == 10650:  # Bộ nhớ trong
                                product_internalmemory = attr['value']

                    product_brand = str(item['brand'])
                    # https://shopee.vn/api/v2/shop/get?is_brief=1&shopid=23220672
                    product_shop = 'Shopee'
                    # shopid = item['shopid']
                    # shoplink = 'https://shopee.vn/api/v2/shop/get?is_brief=1&shopid=%s' % shopid
                    # if shoplink is not None:
                    #     yield scrapy.Request(shoplink, callback=self.get_shop_name)

                    product_rates = item['item_rating']['rating_star']
                    product_location = str(item['shop_location'])
                    product_sku = str(item['itemid'])
                    product_instock = 1
                    instock = item['stock']
                    if instock <= 0:
                        product_instock = 0  # Out of stock

                    products = ProductItem(
                        cid='dienthoai',  # 1: Smartphone
                        title=product_title,
                        description=product_desc,
                        oldprice=product_oldprice,
                        price=product_price,
                        swatchcolors=product_swatchcolors,
                        internalmemory=product_internalmemory,
                        specifications=product_specifications,
                        link=product_link,
                        images=product_images,
                        brand=product_brand,
                        shop=product_shop,
                        rates=product_rates,
                        location=product_location,
                        domain='shopee.vn',
                        sku=product_sku,
                        instock=product_instock,
                        body=''
                    )

                    yield products

        except json.JSONDecodeError as ex:
            logger.error('Could not parse json data. Errors %s' % ex)
        pass

    def get_shop_name(self, response):
        # https://shopee.vn/api/v2/shop/get?is_brief=1&shopid=23220672
        shop_name = 'Shopee'
        try:
            json_data = json.loads(response.body, encoding='utf-8')
            if json_data is not None:
                item = json_data['data']
                if item is not None:
                    shop_name = item['name']
                    if shop_name is None:
                        shop_name = item['account']['username']
        except Exception as ex:
            logger.error('Could not parse shop name. Errors %s' % ex)

        yield shop_name

    def parse_money(self, value):
        try:
            if str(value).isdigit():
                return value
            return re.sub(r'[^\d]', '', str(value))
        except Exception as ex:
            logger.error('parse_money errors: %s' % ex)
