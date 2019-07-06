# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from ..items import ProductItem

logger = logging.getLogger(__name__)


class HnammobileSpider(CrawlSpider):
    name = 'hnammobile'
    allowed_domains = ['www.hnammobile.com']
    start_urls = ['https://www.hnammobile.com/dien-thoai/']

    def parse(self, response):
        for product_link in response.css('div.image>a::attr(href)'):
            yield response.follow(product_link, callback=self.parse_product_detail)
        pass

    def parse_product_detail(self, response):

        def extract_with_css(query):
            return response.css(query).get(default='').strip()

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_price():
            price = response.css(
                'p.special-price>span::text').get(default='').strip()
            if price == '':
                price = response.css(
                    'span.regular-price>span::text').get(default='').strip()
            return price

        def extract_product_gallery():
            gallery = response.css(
                'div.product-image-gallery>img::attr(src)').getall()
            if len(gallery) <= 0:
                gallery = response.css(
                    'div.product-img-box>img::attr(src)').get()
            return gallery

        # Validate price with pattern
        price_pattern = re.compile("([0-9](\\w+ ?)*\\W+)")
        product_price = extract_price()
        if re.match(price_pattern,product_price) is None:
            return

        product_title = extract_with_css('h1::text')
        product_desc = extract_with_xpath('//meta[@name="description"]/@content')
        product_swatchcolors = response.css(
            'label.opt-label>span::text').getall()
        product_images = extract_product_gallery()
        product_specifications = response.xpath(
            '//*[@id="tskt"]/tr/*/text()').re('(\\w+[^\n]+)')

        product_link = response.url
        products = ProductItem()
        products['title'] = product_title
        products['description'] = product_desc
        products['price'] = product_price
        products['swatchcolors'] = product_swatchcolors
        products['specifications'] = product_specifications
        products['link'] = product_link
        products['images'] = product_images

        yield products
        pass
