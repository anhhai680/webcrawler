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


class TikiSpider(scrapy.Spider):
    name = 'tiki'
    allowed_domains = ['tiki.vn']
    start_urls = ['https://tiki.vn/dien-thoai-smartphone/c1795']
    # rules = (
    #     Rule(LinkExtractor(
    #         allow=(
    #             '/dien-thoai-smartphone/',
    #             '/dien-thoai-smartphone/[\\w-]+/[\\w-]+$'
    #         ),
    #         deny=(
    #             '/tin-tuc/',
    #             '/phu-kien/',
    #             '/huong-dan/',
    #             '/ho-tro/',
    #             '/tra-gop/',
    #             '/khuyen-mai/',
    #             '/tel:19006035',
    #             '/tel:18006963',
    #             '/top/',
    #             '/dat-ve-may-bay?src=(.*?)',
    #             '/chuong-trinh/',
    #             '/phieu-qua-tang/'
    #             '/deal-hot?src=(.*?)',
    #         ),
    #         allow_domains=['tiki.vn']
    #     ), callback='parse_tiki'),
    # )

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'webcrawler.middlewares.tiki.TikiSpiderMiddleware': 543
        },
    }

    def __init__(self, limit_pages=None, *args, **kwargs):
        super(TikiSpider, self).__init__(*args, **kwargs)
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 300

    def parse(self, response):
        logger.info('Scrape url: %s' % response.url)
        for product_link in response.xpath('//div[@class="product-box-list"]/div/a/@href').getall():
            yield response.follow(product_link, callback=self.parse_product_detail)

        # Following next page to scrape
        next_page = response.xpath(
            '//link[@rel="next"]/@href').get()
        if next_page is not None:
            match = re.match(r".*?page=(\d+)", next_page)
            if match is not None:
                next_page_number = int(match.groups()[0])
                if next_page_number <= self.limit_pages:
                    yield response.follow(next_page, callback=self.parse)
                else:
                    logger.info('Spider will be stop here.{0} of {1}'.format(
                        next_page_number, next_page))

        pass

    def parse_product_detail(self, response):

        logger.info('parse_product_detail link: %s' % response.url)

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_xpath_all(query):
            return response.xpath(query).getall()

        try:

            product_link = response.url
            product_title = extract_with_xpath(
                '//h1[@class="item-name"]/span/text()')
            product_desc = extract_xpath_all(
                '//div[@class="top-feature-item bullet-wrap"]/p/text()')
            product_desc = ''.join(product_desc)
            # product_swatchcolors = extract_swatchcolors(
            #     '//div[@class="product_pick_color"]/div[contains(@class,"prco_content")]/div[contains(@class,"color color_cover")]/a//text()')

            #product_sku = extract_with_xpath('//div[@id="product-sku"]/p/text()')
            sku = re.findall(r'p\d+', product_link)
            if len(sku) > 0:
                product_sku = sku[0]
            product_price = 0
            product_oldprice = extract_with_xpath(
                '//p[@id="p-listpirce"]/@data-value')
            if product_oldprice is not None and product_oldprice != '':
                product_oldprice = self.parse_money(product_oldprice)
            else:
                product_oldprice = 0

            product_images = None
            product_swatchcolors = None
            product_internalmemory = extract_with_xpath(
                '//td[@rel="rom"]/../td[@class="last"]/text()')
            product_specifications = []
            product_brand = extract_with_xpath(
                '//div[@class="item-brand"]/p/a/text()')
            product_shop = extract_with_xpath(
                '//div[@class="current-seller"]/div/div/span/text()')
            product_location = 'Hồ Chí Minh'
            # product_shipping = 0  # 1 Free shipping, 0 Not Free
            product_rates = None
            rates = extract_with_xpath(
                '//meta[@itemprop="ratingValue"]/@content')
            if rates is not None and rates != '':
                product_rates = rates
            else:
                product_rates = 0

            product_instock = 1  # Product in stock

            # product_specifications = []
            for srow in response.xpath('//table[@id="chi-tiet"]/tbody/tr'):
                if srow is not None:
                    try:
                        spec_values = srow.xpath('.//td//text()').getall()
                        spec_info = [st.strip()
                                     for st in spec_values if st.strip()]
                        product_specifications.append(spec_info)
                    except:
                        pass

            # parse json data from response
            script = response.xpath(
                '//script/text()').re('var configuration = ({.*?});')
            if len(script) > 0:
                json_data = json.loads(script[0])
                if len(json_data) > 0:
                    # if len(json_data["configurable_options"]) > 0:
                    #     product_swatchcolors = [
                    #         color["label"] for color in json_data["configurable_options"][0]["values"]]
                    if len(json_data["configurable_products"]) > 0:
                        for item in json_data["configurable_products"]:
                            product_title = item['name']
                            product_price = item['price']
                            product_images = [img["large_url"]
                                              for img in item["images"]]
                            inventory_status = item['inventory_status']
                            if inventory_status is not None:
                                if inventory_status == 'available':
                                    product_instock = 1
                                else:
                                    product_instock = 0  # Out of
                            # if 'option1' in item and 'option2' not in item:
                            #     product_swatchcolors = item['option1']
                            # elif 'option2' in item:
                            #     product_swatchcolors = item['option2']
                            # else:
                            #     product_swatchcolors = item['color']

                            if 'option1' in item:
                                if 'GB' not in item['option1']:
                                    product_swatchcolors = item['option1']
                            elif 'option2' in item:
                                if 'GB' not in item['option2']:
                                    product_swatchcolors = item['option2']
                            elif 'color' in item:
                                product_swatchcolors = item['color']

                            spid = item['id']
                            product_link = re.sub(
                                r'spid=(.*)', 'spid=%s' % spid, product_link)

                            products = ProductItem()
                            products['cid'] = 'dienthoai'  # 1: Smartphone
                            products['title'] = product_title
                            products['description'] = product_desc
                            products['oldprice'] = int(product_oldprice)
                            products['price'] = product_price
                            products['swatchcolors'] = product_swatchcolors
                            products['internalmemory'] = product_internalmemory
                            products['specifications'] = product_specifications
                            products['link'] = product_link
                            products['images'] = product_images
                            products['brand'] = product_brand
                            products['shop'] = product_shop
                            products['rates'] = float(product_rates)
                            products['location'] = product_location
                            products['domain'] = 'tiki.vn'
                            products['sku'] = product_sku
                            products['instock'] = product_instock
                            products['body'] = ''

                            yield products
        except Exception as ex:
            logger.error('Tiki parse_product_detail errors: %s' % ex)

    def parse_money(self, value):
        try:
            if str(value).isdigit():
                return value
            return re.sub(r'[^\d]', '', str(value))
        except Exception as ex:
            logger.error('parse_money errors: %s' % ex)
