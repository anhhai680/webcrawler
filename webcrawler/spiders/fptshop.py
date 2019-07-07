# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from ..items import ProductItem


logger = logging.getLogger(__name__)

class FptshopSpider(CrawlSpider):
    name = 'fptshop'
    allowed_domains = ['fptshop.com.vn']
    start_urls = ['https://fptshop.com.vn/dien-thoai']
    rules = (
        Rule(LxmlLinkExtractor(
            allow=(
                '/dien-thoai/',
                '/dien-thoai/[\\w-]+/[\\w-]+$'
            ),
            deny=(
                '/dien-thoai/#',
                '/tin-tuc/',
                '/ctkm/(.*?)',
                '/phu-kien/',
                '/huong-dan/',
                '/ho-tro/',
                '/tra-gop',
                '/kiem-tra-bao-hanh?tab=thong-tin-bao-hanh',
                '/cua-hang',
                '/kiem-tra-hang-apple-chinh-hang',
                '/ffriends',
                '/khuyen-mai',
                '/sim-so-dep',
                'tel:18006601',
                'tel:18006616'
            ),
            deny_domains=(
                'vieclam.fptshop.com.vn',
                'online.gov.vn',
                'hangmy.fptshop.com.vn'
            ),
        ), callback='parse_fptshop'),
    )

    def parse_fptshop(self, response):
        logger.info('Scrape url: %s' % response.url)
        for link in response.xpath('//div[@class="owl-item active"]/div[@class="item"]/a/@href'):
            product_link = "https://fptshop.com.vn/%s" % link
            yield response.follow(product_link, callback=self.parse_product_detail)
        
        next_page = response.xpath(
            '//li[contains(@class,"pagination-item") and (not(contains(@class,"active")))]/a/@href').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse_fptshop)
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
            '//div[contains(@class,"fs-pr-box")]/p[@class="fs-dtprice"]/text()')
        if re.match(price_pattern, product_price) is None:
            return

        product_title = extract_with_xpath('//h1[@class="fs-dttname"]/text()')
        product_desc = extract_with_xpath(
            '//meta[@name="description"]/@content')
        product_swatchcolors = extract_swatchcolors(
            '//div[@class="fs-dticolor fs-dticolor-img"]/ul/li/span/@title')
        product_images = extract_product_gallery(
            '//div[@class="owl-stage-outer"]/div[@class="owl-stage"]/div[@class="owl-item active"]/div[@class="item"]/div/a/img/@src')
        product_specifications = response.xpath('//div[@class="fs-tsright"]/ul/li/*/text()').getall()


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
