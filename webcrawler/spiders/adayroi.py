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


class AdayroiSpider(CrawlSpider):
    name = 'adayroi'
    allowed_domains = ['www.adayroi.com']
    start_urls = ['https://www.adayroi.com/dien-thoai-c323']
    rules = (
        Rule(LxmlLinkExtractor(
            allow=(
                '/dien-thoai-c323',
            ),
            deny=(
                '/tin-tuc/',
                '/phu-kien/',
                '/huong-dan/',
                '/ho-tro/',
                '/tra-gop/',
                '/khuyen-mai/',
                '/top/',
                '/chuong-trinh/',
                '/phieu-qua-tang/'
            ),
        ), callback='parse_adayroi'),
    )

    # custom_settings = {
    #     'DOWNLOADER_MIDDLEWARES': {
    #         'webcrawler.middlewares.adayroi.AdayroiSpiderMiddleware': 543
    #     }
    # }

    def __init__(self, limit_pages=None, *args, **kwargs):
        super(AdayroiSpider, self).__init__(*args, **kwargs)
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 300

    def parse_adayroi(self, response):
        logger.info('Scrape url: %s' % response.url)
        for product_link in response.css('div.product-item__container>a.product-item__thumbnail::attr(href)').getall():
            product_link = "https://www.adayroi.com%s" % product_link
            yield response.follow(product_link, callback=self.parse_product_detail)

        # Following next page to scrape
        # next_page = response.css('section.section__pagination>nav.navigation>ul.hidden-xs').xpath(
        #     './/li[not(contains(@class,"active"))]/a[not(contains(@class,"btn disabled"))]/@href').get()
        next_page = response.xpath('//a[@rel="next"]/@href').get()
        if next_page is not None:
            match = re.match(r".*?page=(\d+)", next_page)
            next_page_number = int(match.groups()[0])
            if next_page_number <= self.limit_pages:
                next_page = "https://www.adayroi.com%s" % next_page
                yield response.follow(next_page, callback=self.parse_adayroi)
        pass

    def parse_product_detail(self, response):

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_price(query):
            price = response.xpath(query).get(default='').strip()
            return price

        def extract_xpath_all(query):
            gallery = response.xpath(query).getall()
            return gallery

        #logger.info('Product Url: %s' % response.url)
        # Validate price with pattern
        price_pattern = re.compile("([0-9](\\w+ ?)*\\W+)")
        product_price = 0
        # regular_prices = extract_price(
        #     '//div[@class="product-detail__price"]/div[@class="product-detail__price-info"]/div[@class="price-info__sale"]/text()')
        regular_prices = extract_with_xpath(
            '//div[contains(@class,"txt-color-5 h1-bo")]/text()')
        #logger.info('Product Price: %s' % product_price)
        if re.match(price_pattern, regular_prices) is None:
            return
        else:
            product_price = self.parse_money(regular_prices)

        product_oldprice = 0
        product_internalmemory = None
        product_brand = None
        product_location = 'Hồ Chí Minh'
        product_rates = 0
        product_sku = None
        product_instock = 1

        product_link = extract_with_xpath(
            '//link[@rel="canonical"]/@href')
        product_title = extract_with_xpath(
            '//div[@class="product-detail__title"]/h1/text()')

        short_desc = extract_xpath_all(
            '//div[@class="short-des__content"]/ul/li/p/text() | //div[@class="short-des__content"]/ul/li/p/span/text()')
        product_desc = ''.join(short_desc)
        #product_desc = extract_with_xpath('//meta[@property="description"]/@content')

        product_swatchcolors = None
        # colors = extract_xpath_all(
        #     '//div[@class="product-variant__list"]/a//text()')
        for crow in response.xpath('//div[@class="product-variant__list"]/a').getall():
            color_link = crow.xpath(
                './/[not(contains(@class,"disabled"))]/@href')
            color_text = crow.xpath('.//span[@class="h6-re"]/text()')
            if color_link is not None:
                if color_link not in response.url:
                    requestUrl = 'https://www.adayroi.com%s' % color_link
                    yield response.follow(requestUrl, callback=self.parse_product_detail)
                else:
                    scolors = color_text.split()
                    if len(scolors) > 0:
                        product_swatchcolors = str(scolors[0])

        product_oldprice = 0
        oldprice = extract_price(
            '//div[@class="txt-color-16 h2-re mxl-8 txt-deco-line_through ng-star-inserted"]/text()')
        if oldprice is not None and oldprice != '':
            product_oldprice = self.parse_money(oldprice)

        product_internalmemory = extract_with_xpath(
            '//td[@class="product-specs__value"]/div[@class="ng-star-inserted"]/text()')

        # product_images = extract_with_xpath('//meta[@property="image"]/@content')
        product_images = []
        media_script = extract_with_xpath(
            '//div[@class="col-sm-6 product-detail__info-block"]/script/text()')
        media_pattern = re.compile(r'^var productJsonMedias = (.*?);\s*')
        medias = media_pattern.findall(media_script)
        if medias is not None and len(medias) > 0:
            json_data = json.loads(medias[0])
            product_images = [item["zoomUrl"] for item in json_data]

        # Specifications product
        product_specifications = extract_xpath_all(
            '//div[@class="product-specs__table"]/table/tbody/tr/td/text()')

        product_brand = extract_with_xpath(
            '//div[@class="txt-color-16 h6-re mt-6 ng-star-inserted"]/span/a[@class="txt-color-25 "]/text()')
        product_shop = extract_with_xpath(
            '//div[@class="txt-color-16 h6-re mt-6 ng-star-inserted"]/span[@class="ng-star-inserted"]/a/text()')
        product_location = 'Hồ Chí Minh'
        product_sku = None
        sku_text = extract_with_xpath(
            '//span[@class="product-sapSku ng-star-inserted"]/text()')
        if sku_text is not None:
            skus = sku_text.split()
            if len(skus) > 0:
                product_sku = str(skus[2])
        product_instock = 1
        outofstock_text = extract_with_xpath(
            '//div[@class="product-price my-8 ng-star-inserted"]/div[contains(@class,"txt-color-16 h1-bo")]/text()')
        if outofstock_text is not None:
            if outofstock_text in 'Tạm hết hàng':
                product_instock = 0

        product_rates = extract_with_xpath(
            '//div[@class="wx-196 flex-col flex-start_center ng-star-inserted"]/div[@class="h41-bo-47"]/text()')

        # product_specifications = []
        # for spec_row in response.xpath('//div[@class="product-specs__table"]/table/tbody/tr'):
        #     if spec_row is not None:
        #         try:
        #             spec_key = spec_row.xpath(
        #                 './/td[@class="specs-table__property"]/text()').get().strip()
        #             spec_value = spec_row.xpath(
        #                 './/td[@class="specs-table__value"]/text()').get().strip()
        #             product_specifications.append({spec_key, spec_value})
        #         except:
        #             pass

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
        products['domain'] = 'adayroi.com'
        products['sku'] = product_sku
        products['instock'] = product_instock
        products['body'] = ''

        yield products

    def parse_money(self, value):
        if str(value).isdigit():
            return value
        return re.sub(r'[^\d]', '', str(value))
