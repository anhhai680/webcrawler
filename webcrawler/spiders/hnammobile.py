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

        def extract_price(query):
            price = response.xpath(query).get(default='').strip()
            return price

        def extract_product_gallery(query):
            gallery = response.xpath(query).getall()
            return gallery
        
        def extract_swatchcolors(query):
            gallery = response.xpath(query).getall()
            return gallery

        # Validate price with pattern
        price_pattern = re.compile("([0-9](\\w+ ?)*\\W+)")
        product_price = extract_price('//h3[contains(@class,"price")]/font/font[@class="numberprice"]/text()')
        if re.match(price_pattern,product_price) is None:
            return

        product_title = extract_with_xpath('//h2[@class="title"]/text()')
        product_desc = extract_with_xpath('//meta[@name="description"]/@content')
        product_swatchcolors = extract_swatchcolors('//div[@class="picker-color row"]/ul/li/div/text()')
        product_images = extract_product_gallery('//div[@class="gallery"]/div[contains(@class,"item")]/@data-src')
        #product_specifications = response.xpath('//*[@id="tskt"]/tr/*/text()').re('(\\w+[^\n]+)')
        product_specifications = []

        for spec_info in response.css('div.content-body>div'):
            if spec_info is not None:
                try:
                    spec_key = spec_info.css('label::text').get().strip()
                    spec_value = spec_info.css('p::text').get().strip()
                    product_specifications.append({spec_key, spec_value})
                except:
                    pass

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
