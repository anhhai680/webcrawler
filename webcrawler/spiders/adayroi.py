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

    def parse_adayroi(self, response):
        logger.info('Scrape url: %s' % response.url)
        for product_link in response.css('div.product-item__container>a.product-item__thumbnail::attr(href)').getall():
            product_link = "https://www.adayroi.com%s" % product_link
            yield response.follow(product_link, callback=self.parse_product_detail)

        # Following next page to scrape
        next_page = response.css('section.section__pagination>nav.navigation>ul.hidden-xs').xpath(
            './/li[not(contains(@class,"active"))]/a[not(contains(@class,"btn disabled"))]/@href').get()
        if next_page is not None:
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

        logger.info('Product Url: %s' % response.url)
        # Validate price with pattern
        price_pattern = re.compile("([0-9](\\w+ ?)*\\W+)")
        product_price = extract_price(
            '//div[@class="product-detail__price"]/div[@class="product-detail__price-info"]/div[@class="price-info__sale"]/text()')
        logger.info('Product Price: %s' % product_price)
        if re.match(price_pattern, product_price) is None:
            return

        product_link = extract_with_xpath(
            '//link[@rel="canonical"]/@href')
        product_title = extract_with_xpath(
            '//div[@class="product-detail__title"]/h1/text()')

        short_desc = extract_xpath_all(
            '//div[@class="short-des__content"]/ul/li/p/text()')
        product_desc = ''.join(short_desc)
        #product_desc = extract_with_xpath('//meta[@property="description"]/@content')

        product_swatchcolors = extract_xpath_all(
            '//div[@class="product-variant__list"]/a//text()')

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
        product_specifications = []
        for spec_row in response.xpath('//div[@class="product-specs__table"]/table/tbody/tr'):
            if spec_row is not None:
                try:
                    spec_key = spec_row.xpath(
                        './/td[@class="specs-table__property"]/text()').get().strip()
                    spec_value = spec_row.xpath(
                        './/td[@class="specs-table__value"]/text()').get().strip()
                    product_specifications.append({spec_key, spec_value})
                except:
                    pass

        products = ProductItem()
        products['cid'] = 1  # 1: Smartphone
        products['title'] = product_title
        products['description'] = product_desc
        products['price'] = product_price
        products['swatchcolors'] = product_swatchcolors
        products['specifications'] = product_specifications
        products['link'] = product_link
        products['images'] = product_images
        products["shop"] = 'adayroi'
        products["domain"] = 'adayroi.com'

        yield products
