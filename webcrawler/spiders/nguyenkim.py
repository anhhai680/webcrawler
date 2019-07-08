# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor


from ..items import ProductItem

logger = logging.getLogger(__name__)


class NguyenkimSpider(CrawlSpider):
    name = 'nguyenkim'
    allowed_domains = ['www.nguyenkim.com']
    start_urls = ['https://www.nguyenkim.com/dien-thoai-di-dong/']
    rules = (
        Rule(LxmlLinkExtractor(
            allow=(
                '/dien-thoai-di-dong/',
                '/dien-thoai-di-dong/[\\w-]+/[\\w-]+$'
            ),
            deny=(
                '/tin-tuc/',
                '/phu-kien/',
                '/huong-dan/',
                '/ho-tro/',
                '/tra-gop/',
                'https://www.nguyenkim.com/cac-trung-tam-mua-sam-nguyen-kim.html',
                '/khuyen-mai/',
            ),
        ), callback='parse_nguyenkim'),
    )

    def parse_nguyenkim(self, response):
        logger.info('Scrape url: %s' % response.url)
        for product_link in response.xpath('//div[@class="item nk-fgp-items"]/a[@class="nk-link-product"]/@href').getall():
            yield response.follow(product_link, callback=self.parse_product_detail)

        # Following next page to scrape
        next_page = response.xpath('//div[@class="NkPaging ty-pagination__items"]/a/@href').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse_nguyenkim)
        pass

    def parse_product_detail(self, response):

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_price(query):
            price = response.xpath(query).get(default='').strip()
            return price

        def extract_product_gallery(query):
            gallery = response.xpath(query).getall()
            return gallery

        def extract_swatchcolors(query):
            swatchcolors = response.xpath(query).getall()
            return swatchcolors

        # Validate price with pattern
        price_pattern = re.compile("([0-9](\\w+ ?)*\\W+)")
        product_price = extract_price(
            '//div[@class="product_info_price_value-final"]/span[@class="nk-price-final"]/text()')
        logger.info('Product Price: %s' % product_price)
        if re.match(price_pattern, product_price) is None:
            return

        product_title = extract_with_xpath('//h1[@class="product_info_name"]/text()')
        product_desc = extract_with_xpath(
            '//meta[@name="description"]/@content')
        product_swatchcolors = extract_swatchcolors(
            '//div[@class="product_pick_color"]/div[contains(@class,"prco_content")]/div[contains(@class,"color color_cover")]/a//text()')
        product_images = extract_product_gallery(
            '//ul[@class="nk-product-bigImg"]/li/div[@class="wrap-img-tag-pdp"]/span/img/@src')
        product_specifications = response.xpath(
            '//table[@class="productSpecification_table"]/tbody/tr/td/text()').getall()

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
