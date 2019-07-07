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
    rules = (
        Rule(LxmlLinkExtractor(
            allow=('/dien-thoai/'),
            deny=(
                '/dien-thoai/#',
                '/tin-tuc/',
                '/may-tinh-bang/',
                '/phu-kien/',
                '/dong-ho-thong-minh/',
                '/kho-sim',
                '/event/',
                '/loai-dien-thoai/',
                '/mua-tra-gop',
                'https://www.hnammobile.com/dien-thoai/tel:19002012',
                'https://www.hnammobile.com/dien-thoai/tel:01234303000'
            )
        ), callback='parse_hnammobile'),
    )
    #handle_httpstatus_list = [404, 504]

    def parse_hnammobile(self, response):
        logger.info('Scrape url: %s' % response.url)
        for product_link in response.css('div.image>a::attr(href)'):
            yield response.follow(product_link, callback=self.parse_product_detail)

        # following pagination next page to scrape
        # links = response.xpath(
        #     '//li[contains(@class,"pagination-item") and (not(contains(@class,"active")))]/a/@href').getall()
        # if len(links) > 0:
        #     for next_page in links:
        #         yield response.follow(next_page, callback=self.parse_hnammobile)
        next_page = response.xpath(
            '//li[contains(@class,"pagination-item") and (not(contains(@class,"active")))]/a/@href').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse_hnammobile)
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
            swatchcolors = response.xpath(query).getall()
            return swatchcolors

        # Validate price with pattern
        price_pattern = re.compile("([0-9](\\w+ ?)*\\W+)")
        product_price = extract_price(
            '//h3[contains(@class,"price")]/font/font[@class="numberprice"]/text()')
        if re.match(price_pattern, product_price) is None:
            return

        product_title = extract_with_xpath('//h2[@class="title"]/text()')
        product_desc = extract_with_xpath(
            '//meta[@name="description"]/@content')
        product_swatchcolors = extract_swatchcolors(
            '//div[@class="picker-color row"]/ul/li/div//text()')
        product_images = extract_product_gallery(
            '//div[@class="gallery"]/div[contains(@class,"item")]/@data-src')
        product_specifications = response.xpath('//div[@class="content-body"]/div[@class="row size-screen"]//text()').getall()

        # for spec_info in response.css('div.content-body>div'):
        #     if spec_info is not None:
        #         try:
        #             spec_key = spec_info.css('label::text').get().strip()
        #             spec_value = spec_info.css('p::text').get().strip()
        #             product_specifications.append({spec_key, spec_value})
        #         except:
        #             pass

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
