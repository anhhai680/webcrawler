# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor


from ..items import ProductItem

logger = logging.getLogger(__name__)


class VnexpressSpider(CrawlSpider):
    name = 'vnexpress'
    allowed_domains = ['shop.vnexpress.net']
    start_urls = ['https://shop.vnexpress.net/dien-thoai']
    rules = (
        Rule(LxmlLinkExtractor(
            allow=(
                '/dien-thoai/',
                '/dien-thoai/[\\w-]+/[\\w-]+$'
            ),
            deny=(
                '/tin-tuc/',
                '/phu-kien/',
                '/retail/',
                '/ho-tro/',
                '/tra-gop/',
                '/khuyen-mai/',
                'https://shop.vnexpress.net/mua-sam-uu-dai',
                'https://shop.vnexpress.net/thuong-hieu-uy-tin',
                'https://shop.vnexpress.net/xu-huong-mua-sam',
                'https://shop.vnexpress.net/cau-hoi-thuong-gap.html',
                'tel:1900633376'
            ),
        ), callback='parse_vnexpress'),
    )
    handle_httpstatus_list = [301]

    def parse_vnexpress(self, response):
        logger.info('Scrape url: %s' % response.url)
        for product_link in response.xpath('//div[@class="item-pro"]/div[@class="box box-image"]/a/@href').getall():
            yield response.follow(product_link, callback=self.parse_product_detail)

        # Following next page to scrape
        next_page = response.xpath(
            '//ul[@class="pagination pagination-lg"]/li/a[not(contains(@class,"active"))]/@href').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse_vnexpress)
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
            '//span[@class="price-current price_sp_detail"]/text()')
        logger.info('Product Price: %s' % product_price)
        if re.match(price_pattern, product_price) is None:
            return

        product_title = extract_with_xpath(
            'normalize-space(//h1[@class="product-title clearfix"]/text())')
        product_desc = extract_with_xpath(
            'normalize-space(//meta[@name="description"]/@content)')
        product_swatchcolors = extract_swatchcolors(
            '//div[@class="similar-products"]/span/@rel')
        product_images = extract_product_gallery(
            '//div[@id="images_pro"]/a/@href')
        product_specifications = response.xpath(
            '//div[@id="information"]/div/table[@class="table"]/tbody/tr/td//text()').getall()

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
