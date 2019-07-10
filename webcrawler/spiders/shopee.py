# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from decimal import Decimal

from ..items import ProductItem

logger = logging.getLogger(__name__)


class ShopeeSpider(CrawlSpider):
    name = 'shopee'
    allowed_domains = ['shopee.vn']
    start_urls = [
        'https://shopee.vn/Điện-thoại-cat.84.1979']
    rules = (
        Rule(LxmlLinkExtractor(
            allow=(
                '(.*?)-cat.84.1979',
            ),
            deny=(
                '/tin-tuc/',
                '/phu-kien/',
                '/huong-dan/',
                '/ho-tro/',
                '/tra-gop/',
                '/khuyen-mai/',
            ),
        ), callback='parse_shopee'),
    )

    def parse_shopee(self, response):
        logger.info('Scrape url: %s' % response.url)
        links = response.xpath('//div[@class="row shopee-search-item-result__items"]/div[@class="col-xs-2-4 shopee-search-item-result__item"]/div/a/@href').getall()
        for product_link in links:
            product_link = "https://shopee.vn%s" % product_link
            yield response.follow(product_link, callback=self.parse_product_detail)

        # Following next page to scrape
        next_page = response.xpath(
            '//div[@class="shopee-page-controller"]/button/text()').get()
        if next_page is not None:
            product_link = response.url + '?page=' + next_page
            yield response.follow(product_link, callback=self.parse_shopee)
        pass

    def parse_product_detail(self, response):

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_price(query):
            price = response.xpath(query).get(default='').strip()
            return price

        logger.info('Product Url: %s' % response.url)
        # Validate price with pattern
        price_pattern = re.compile("(\\S*[0-9](\\w+ ?))")
        # product_price = extract_price(
        #     '//div[@class="items-center"]/div[@class="_3n5NQx"]/text()')
        product_price = response.css('div.items-center>div._3n5NQx::text').get()
        logger.info('Product Price: %s' % product_price)
        if re.match(price_pattern, product_price) is None:
            return

        product_title = response.css('div.qaNIZv::text').get()
        product_desc = extract_with_xpath(
            '//meta[@name="description"]/@content')
        product_swatchcolors = []
        product_images = extract_with_xpath(
            '//meta[@name="image"]/@content')

        # product_specifications = response.xpath(
        #     '//table[@class="productSpecification_table"]/tbody/tr/td/text()').getall()
        product_specifications = []
        for item in response.xpath('//div[@class="_2aZyWI"]/div[@class="kIo6pj"]'):
            try:
                key = item.xpath('.//label/text()').get()
                value = item.xpath('.//a/text()').get()
                product_specifications.append({key, value})
            except:
                pass

        product_link = response.url
        products = ProductItem()
        products['title'] = product_title
        products['description'] = product_desc
        products['price'] = self.parse_money(product_price)
        products['swatchcolors'] = product_swatchcolors
        products['specifications'] = product_specifications
        products['link'] = product_link
        products['images'] = product_images

        yield products
    
    def parse_money(self,value):
        yield re.sub(r'[^\d.]','',value)
